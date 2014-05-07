#This file is part magento_manufacturer module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.modules.product_esale.tools import slugify

from magento import *
import logging

__all__ = ['MagentoApp']
__metaclass__ = PoolMeta

class MagentoApp:
    __name__ = 'magento.app'

    from_products = fields.DateTime('From Products', 
        help='This date is the range to import (filter)')
    to_products = fields.DateTime('To Products', 
        help='This date is the range from import (filter)')
    category_root_id = fields.Integer('Category Root',
        help='Category Root ID Magento')

    @classmethod
    def __setup__(cls):
        super(MagentoApp, cls).__setup__()
        cls._error_messages.update({
                'select_category_root': 'Select Category Root ID in Magento APP!',
                })
        cls._buttons.update({
                'core_import_product_type': {},
                'core_import_group_attributes': {},
                'core_import_categories': {},
                'core_import_products': {},
                'core_import_images': {},
                })

    @classmethod
    @ModelView.button
    def core_import_product_type(self, apps):
        """Import Magento Product Type to Tryton
        Only create new products type; not update or delete
        """
        ProductType = Pool().get('magento.product.type')
        for app in apps:
            with ProductTypes(app.uri,app.username,app.password) as product_type_api:
                for product_type in product_type_api.list():
                    prod_types = ProductType.search([
                        ('code','=',product_type['type']),
                        ])
                    if not len(prod_types) > 0: #create
                        values = {
                            'name': product_type['label'],
                            'code': product_type['type'],
                        }
                        ptype = ProductType.create([values])[0]
                        logging.getLogger('magento').info(
                            'Create Product Type: App %s, Type %s, ID %s.' % (
                            app.name, 
                            product_type['type'],
                            ptype,
                            ))
                    else:
                        logging.getLogger('magento').info(
                            'Skip! Product Type %s exists' % (
                            product_type['type'],
                            ))

    @classmethod
    @ModelView.button
    def core_import_group_attributes(self, apps):
        """Import Magento Group Attributes to Tryton
        Only create new groups; not update or delete
        """
        ExternalReferential = Pool().get('magento.external.referential')
        AttrGroup = Pool().get('esale.attribute.group')
        to_create = []
        for app in apps:
            with ProductAttributeSet(app.uri,app.username,app.password) as \
                    product_attribute_set_api:
                for product_attribute_set in product_attribute_set_api.list():
                    attribute_set = ExternalReferential.get_mgn2try(
                        app,
                        'esale.attribute.group',
                        product_attribute_set['set_id'],
                        )

                    if not attribute_set: #create
                        to_create.append({
                            'name': product_attribute_set['name'],
                            'code': product_attribute_set['name'],
                        })
                    else:
                        logging.getLogger('magento').info(
                            'Skip! Attribute Group exists: APP %s, Attribute %s.' % (
                            app.name, 
                            product_attribute_set['set_id'],
                            ))

        if to_create:
            attribute_groups = AttrGroup.create(to_create)
            for attribute_group in attribute_groups:
                ExternalReferential.set_external_referential(
                    app,
                    'esale.attribute.group',
                    attribute_group.id,
                    product_attribute_set['set_id'],
                    )
                logging.getLogger('magento').info(
                    'Create Attribute Group: APP %s, Attribute %s.' % (
                    app.name, 
                    product_attribute_set['set_id'],
                    ))

    def save_menu(app, data, parent=None, menu=None):
        '''
        Save Menu
        :param app: object
        :param data: dict
        :param parent: id
        :param menu: object
        :return: object
        '''
        Menu = Pool().get('esale.catalog.menu')

        action = 'update'
        default_sort_by = data.get('default_sort_by', '')
        if default_sort_by == 'None':
            default_sort_by = ''
        slug = data.get('url_key')
        if not slug:
            slug = slugify(data.get('name'))
        metadescription = data.get('meta_description')
        if metadescription and len(metadescription) > 155:
            metadescription = '%s...' % (metadescription[:152])
        metakeyword = data.get('meta_keywords')
        if metakeyword and len(metakeyword) > 155:
            metakeyword = '%s...' % (metakeyword[:152])
        metatitle = data.get('meta_title')
        if metatitle and len(metatitle) > 155:
            metatitle = '%s...' % (metatitle[:152])

        if not menu:
            menu = Menu()
            action = 'create'

        menu.name = data.get('name')
        menu.parent = parent
        menu.active = data.get('is_active')
        menu.default_sort_by = default_sort_by
        menu.slug = slug
        menu.description = data.get('description')
        menu.metadescription = metadescription
        menu.metakeyword = metakeyword
        menu.metatitle = metatitle
        menu.magento_app = app.id
        menu.magento_id = data.get('category_id')
        menu.save()

        logging.getLogger('magento').info(
            '%s category %s (%s)' % (action.capitalize(), menu.name, menu.id))
        return menu

    @classmethod
    def children_categories(self, app, parent, data):
        '''
        Get recursive categories and create new categories
        :param app: object
        :param parent: id
        :param data: dict
        :return: True
        '''
        Menu = Pool().get('esale.catalog.menu')

        with Category(app.uri, app.username, app.password) as category_api:
            for children in data.get('children'):
                categories = Menu.search([
                        ('magento_app', '=', app.id),
                        ('magento_id', '=', children.get('category_id')),
                        ], limit=1)

                cat_info = category_api.info(children.get('category_id'))
                if categories:
                    category, = categories
                    category = self.save_menu(app, cat_info, parent, category)
                if not categories:
                    category = self.save_menu(app, cat_info, parent)

                if children.get('children'):
                    data = category_api.tree(parent_id=children.get('category_id'))
                    self.children_categories(app, category.id, data)

    @classmethod
    @ModelView.button
    def core_import_categories(self, apps):
        """Import Magento Categories to Tryton
        Only create new categories; not update or delete
        """
        Menu = Pool().get('esale.catalog.menu')

        for app in apps:
            logging.getLogger('magento').info(
                'Start import categories %s' % (app.name))
            if not app.category_root_id:
                self.raise_user_error('select_category_root')

            with Category(app.uri, app.username, app.password) as category_api:
                data = category_api.tree(parent_id=app.category_root_id)

                category_roots = Menu.search([
                        ('magento_app', '=', app.id),
                        ('magento_id', '=', data.get('category_id')),
                        ], limit=1)

                if not category_roots:
                    root_info = category_api.info(data.get('category_id'))
                    category_root = self.save_menu(app, root_info)
                    category_root.active = True
                    category_root.save()
                else:
                    category_root, = category_roots

                self.children_categories(app, category_root.id, data)

            logging.getLogger('magento').info(
                'End import categories %s' % (app.name))

    @classmethod
    @ModelView.button
    def core_import_products(self, apps):
        """Import Magento Products to Tryton
        Create/Update products in Tryton from Magento
        """
        for app in apps:
            #TODO
            pass

    @classmethod
    @ModelView.button
    def core_import_images(self, apps):
        """Import Magento Images to Tryton
        Only create new images; not update or delete
        """
        for app in apps:
            #TODO
            pass

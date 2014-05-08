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

    from_date_products = fields.DateTime('From Date Products', 
        help='This date is the range to import (filter)')
    to_date_products = fields.DateTime('To Date Products', 
        help='This date is the range from import (filter)')
    from_id_products = fields.Integer('From ID Products', 
        help='This Integer is the range to import (filter)')
    to_id_products = fields.Integer('To ID Products', 
        help='This Integer is the range from import (filter)')
    category_root_id = fields.Integer('Category Root',
        help='Category Root ID Magento')
    template_mapping = fields.Many2One('base.external.mapping',
        'Template Mapping', help='Product Template mapping values')
    product_mapping = fields.Many2One('base.external.mapping',
        'Product Mapping', help='Product Product mapping values')
    tax_include = fields.Boolean('Tax Include')

    @classmethod
    def __setup__(cls):
        super(MagentoApp, cls).__setup__()
        cls._error_messages.update({
                'select_category_root': 'Select Category Root ID in Magento APP!',
                'select_store_view': 'Select Store View in Magento APP!',
                'not_import_products': 'Not import products because Magento return '
                    'an empty list of products',
                'import_magento_website': 'First step is Import Magento Store',
                'select_mapping': 'Select Mapping in Magento APP!',
                'select_rang_product_ids': 'Select Product ID From and ID To!',
                'magento_api_error': 'Magento API Error!',
                })
        cls._buttons.update({
                'core_import_product_type': {},
                'core_import_group_attributes': {},
                'core_import_categories': {},
                'core_import_products': {},
                'core_import_product_links': {},
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
        attribute_sets = []
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
                        attribute_sets.append({
                            'name': product_attribute_set['name'],
                            'code': product_attribute_set['name'],
                            'id': product_attribute_set['set_id']
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
                for attribute in attribute_sets:
                    if attribute.get('code') == attribute_group.code:
                        external_id = attribute.get('id')
                        break
                if not external_id:
                    continue
                ExternalReferential.set_external_referential(
                    app,
                    'esale.attribute.group',
                    attribute_group.id,
                    external_id,
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
        Only create/update new categories; not delete
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
        Create/Update new products; not delete
        """
        pool = Pool()
        ProductProduct = pool.get('product.product')
        ProductTemplate = pool.get('product.template')
        BaseExternalMapping = pool.get('base.external.mapping')
        Menu = pool.get('esale.catalog.menu')

        for app in apps:
            if not app.magento_default_storeview:
                self.raise_user_error('select_store_view')
            store_view = app.magento_default_storeview.code

            if not app.magento_websites:
                self.raise_user_error('import_magento_website')

            if not app.magento_websites or not app.product_mapping:
                self.raise_user_error('select_mapping')
            template_mapping = app.template_mapping.name
            product_mapping = app.product_mapping.name

            logging.getLogger('magento').info(
                'Start import products %s' % (app.name))

            with Product(app.uri, app.username, app.password) as product_api:
                ofilter = {}
                data = {}
                products = []

                if app.from_date_products and app.to_date_products:
                    ofilter = {
                        'created_at': {
                            'from': app.from_date_products,
                            'to': app.to_date_products,
                            },
                        }
                    ofilter2 = {
                        'updated_at': {
                            'from': app.from_date_products,
                            'to': app.to_date_products},
                        }
                    products_created = product_api.list(ofilter, store_view)
                    products_updated = products+product_api.list(ofilter2, store_view)
                    products = products_created + products_updated
                    ofilter = dict(ofilter.items() + ofilter2.items())
                    data = {
                        'from_date_products': app.to_date_products,
                        'to_date_products': None,
                        }

                if app.from_id_products and app.to_id_products:
                    ofilter = {
                        'entity_id': {
                            'from': app.from_id_products,
                            'to': app.to_id_products,
                            },
                        }
                    products = product_api.list(ofilter, store_view)
                    data = {
                        'from_id_products': app.to_id_products + 1,
                        'to_id_products': None,
                        }

                if not products:
                    self.raise_user_error('not_import_products')

                logging.getLogger('magento').info(
                    'Import Magento %s products: %s' % (len(products), ofilter))

                # Update last import
                self.write([app], data)

                for product in products:
                    code = product.get('sku')

                    prods = ProductProduct.search([
                            ('code', '=', product.get('sku')),
                            ], limit=1)
                    if prods:
                        prod, = prods

                    product_info = product_api.info(code, store_view)

                    # get values using base external mapping
                    tvals = BaseExternalMapping.map_external_to_tryton(template_mapping, product_info)
                    pvals = BaseExternalMapping.map_external_to_tryton(product_mapping, product_info)

                    # Shops - websites
                    shops = ProductProduct.magento_product_esale_saleshops(app, product_info)
                    if shops:
                        tvals['esale_saleshops'] = shops

                    # Taxes and list price and cost price with or without taxes
                    tax_include = app.tax_include
                    customer_taxes, list_price, cost_price = ProductProduct.magento_product_esale_taxes(app, product_info, tax_include)
                    if customer_taxes:
                        tvals['customer_taxes'] = customer_taxes
                    if not list_price:
                        list_price = product_info.get('price')
                    tvals['list_price'] = list_price
                    if not cost_price:
                        cost_price = product_info.get('price')
                    tvals['cost_price'] = cost_price

                    # Categories -> menus
                    menus = Menu.search([
                            ('magento_app', '=', app.id),
                            ('magento_id', 'in', product_info.get('category_ids')),
                            ])
                    if menus:
                        tvals['esale_menus'] = [menu.id for menu in menus]

                    if app.debug:
                        logging.getLogger('magento').info(
                            'Product values: %s' % (dict(tvals.items() + pvals.items())))

                    if not prods:
                        template = ProductTemplate()
                        action = 'create'
                    else:
                        template = prod.template
                        action = 'update'

                    for key, value in tvals.iteritems():
                        setattr(template, key, value)

                    if not prods:
                        product = ProductProduct()
                    else:
                        product = prod

                    for key, value in pvals.iteritems():
                        setattr(product, key, value)

                    template.products = [product]
                    template.save()
                    logging.getLogger('magento').info(
                        '%s product %s (%s)' % (action.capitalize(), template.rec_name, template.id))

            logging.getLogger('magento').info(
                'End import products %s' % (app.name))

    @classmethod
    @ModelView.button
    def core_import_product_links(self, apps):
        """Import Magento Product Links to Tryton
        Create/Update new products
        """

        self.raise_user_error('magento_api_error') #TODO: delete this line

        for app in apps:
            logging.getLogger('magento').info(
                'Start import product links %s' % (app.name))

            #~ with ProductLinks(app.uri, app.username, app.password) as product_links_api:
                #~ products = []

                #~ if not app.from_id_products and not app.to_id_products:
                    #~ self.raise_user_error('select_rang_product_ids')

                #~ for product_id in range(app.from_id_products, app.to_id_products+1):
                    #~ relateds = product_links_api.list(str(product_id), 'related')
                    #~ up_sells = product_links_api.list(str(product_id), 'up_sell')
                    #~ cross_sells = product_links_api.list(str(product_id), 'cross_sell')

                    #TODO: save product links

            logging.getLogger('magento').info(
                'End import product links %s' % (app.name))


    @classmethod
    @ModelView.button
    def core_import_images(self, apps):
        """Import Magento Images to Tryton
        Only create new images; not update or delete
        """
        for app in apps:
            #TODO
            pass

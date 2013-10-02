#This file is part magento_manufacturer module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta

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

    @classmethod
    def __setup__(cls):
        super(MagentoApp, cls).__setup__()
        cls._buttons.update({
                'core_import_product_type': {},
                'core_import_group_attributes': {},
                'core_import_categories': {},
                'core_import_products': {},
                'core_import_images': {},
                })

        return True

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

    @classmethod
    @ModelView.button
    def core_import_categories(self, apps):
        """Import Magento Categories to Tryton
        Only create new categories; not update or delete
        """
        for app in apps:
            #TODO
            pass

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

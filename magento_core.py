#This file is part magento_manufacturer module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.tools import safe_eval, datetime_strftime
from trytond.transaction import Transaction
from trytond.pool import Pool

from magento import *
import logging

class MagentoApp(ModelSQL, ModelView):
    _name = 'magento.app'
    _description = __doc__

    from_products = fields.DateTime('From Products', 
        help='This date is the range to import (filter)')
    to_products = fields.DateTime('To Products', 
        help='This date is the range from import (filter)')

    def __init__(self):
        super(MagentoApp, self).__init__()
        self._buttons.update({
                'core_import_product_type': {},
                'core_import_group_attributes': {},
                'core_import_categories': {},
                'core_import_products': {},
                'core_import_images': {},
                })

        return True

    @ModelView.button
    def core_import_product_type(self, ids):
        """Import Magento Product Type to Tryton
        Only create new products type; not update or delete
        """
        magento_product_type_obj = Pool().get('magento.product.type')
        for app in self.browse(ids):
            with ProductTypes(app.uri,app.username,app.password) as product_type_api:
                for product_type in product_type_api.list():
                    prod_types = magento_product_type_obj.search([
                        ('code','=',product_type['type']),
                        ])
                    if not len(prod_types) > 0: #create
                        values = {
                            'name': product_type['label'],
                            'code': product_type['type'],
                        }
                        ptype = magento_product_type_obj.create(values)
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
        return True

    @ModelView.button
    def core_import_group_attributes(self, ids):
        """Import Magento Group Attributes to Tryton
        Only create new groups; not update or delete
        """
        magento_external_referential_obj = Pool().get('magento.external.referential')
        for app in self.browse(ids):
            with ProductAttributeSet(app.uri,app.username,app.password) as product_attribute_set_api:
                for product_attribute_set in product_attribute_set_api.list():
                    attribute_set = magento_external_referential_obj.get_mgn2try(
                        app,
                        'esale.attribute.group',
                        product_attribute_set['set_id'],
                        )

                    if not attribute_set: #create
                        values = {
                            'name': product_attribute_set['name'],
                            'code': product_attribute_set['name'],
                        }
                        attribute_group = Pool().get('esale.attribute.group').create(values)
                        magento_external_referential_obj.set_external_referential(
                            app,
                            'esale.attribute.group',
                            attribute_group,
                            product_attribute_set['set_id'],
                            )
                        logging.getLogger('magento').info(
                            'Create Attribute Group: APP %s, Attribute %s.' % (
                            app.name, 
                            product_attribute_set['set_id'],
                            ))
                    else:
                        logging.getLogger('magento').info(
                            'Skip! Attribute Group exists: APP %s, Attribute %s.' % (
                            app.name, 
                            product_attribute_set['set_id'],
                            ))
        return True

    @ModelView.button
    def core_import_categories(self, ids):
        """Import Magento Categories to Tryton
        Only create new categories; not update or delete
        """
        for app in self.browse(ids):
            #TODO
            return True
        return True

    @ModelView.button
    def core_import_products(self, ids):
        """Import Magento Products to Tryton
        Create/Update products in Tryton from Magento
        """
        for app in self.browse(ids):
            #TODO
            return True
        return True

    @ModelView.button
    def core_import_images(self, ids):
        """Import Magento Images to Tryton
        Only create new images; not update or delete
        """
        for app in self.browse(ids):
            #TODO
            return True
        return True

MagentoApp()

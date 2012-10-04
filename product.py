#This file is part magento_product module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval

class MagentoProductType(ModelSQL, ModelView):
    'Magento Product Type'
    _name = 'magento.product.type'
    _description = __doc__

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True,
        help='Same name Magento product type, (example: simple)')
    active = fields.Boolean('Active',
        help='If the active field is set to False, it will allow you to hide the product without removing it.')

    def default_active(self):
        return True

MagentoProductType()

class Product(ModelSQL, ModelView):
    _name = 'product.product'

    def get_magento_product_type(self):
        magento_product_type_obj = Pool().get('magento.product.type')
        ids = magento_product_type_obj.search([
            ('active', '=', True),
            ], order=[('id', 'DESC')])
        product_types = magento_product_type_obj.read(ids, ['code', 'name'])
        return [(pt['code'], pt['name']) for pt in product_types]

    magento_product_type = fields.Selection('get_magento_product_type', 'Product Type',
        states={
            'required': Eval('esale_available', True),
        },
        depends=['esale_available'])

    def default_magento_product_type(self):
        product_type = ''
        magento_product_type_obj = Pool().get('magento.product.type')
        ids = magento_product_type_obj.search([
            ('code', '=', 'simple'),
            ('active', '=', True),
            ])
        if len(ids)>0:
            product_type = 'simple'
        return product_type

Product()

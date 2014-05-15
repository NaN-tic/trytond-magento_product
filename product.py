#This file is part magento_product module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['MagentoProductType', 'Template']
__metaclass__ = PoolMeta


class MagentoProductType(ModelSQL, ModelView):
    'Magento Product Type'
    __name__ = 'magento.product.type'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True,
        help='Same name Magento product type, (example: simple)')
    active = fields.Boolean('Active',
        help='If the active field is set to False, it will allow you to hide the product without removing it.')

    @staticmethod
    def default_active():
        return True


class Template:
    __name__ = 'product.template'

    @classmethod
    def get_magento_product_type(cls):
        ProductType = Pool().get('magento.product.type')
        records = ProductType.search([
            ('active', '=', True),
            ], order=[('id', 'DESC')])
        if not records:
            return [(None, '')]
        product_types = ProductType.read(records, ['code', 'name'])
        return [(pt['code'], pt['name']) for pt in product_types]

    magento_product_type = fields.Selection('get_magento_product_type', 'Product Type',
        states={
            'required': Eval('esale_available', True),
        },
        depends=['esale_available'])
    magento_group_price = fields.Boolean('Magento Grup Price',
        help='If check this value, when export product prices (and shop '
            'is active group price), export prices by group')

    @staticmethod
    def default_magento_product_type():
        product_type = ''
        ProductType = Pool().get('magento.product.type')
        ids = ProductType.search([
            ('code', '=', 'simple'),
            ('active', '=', True),
            ])
        if len(ids)>0:
            product_type = 'simple'
        return product_type

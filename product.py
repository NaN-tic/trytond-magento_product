# This file is part magento_product module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Or

__all__ = ['MagentoProductType', 'MagentoAttributeConfigurable', 
    'Template', 'Product']
__metaclass__ = PoolMeta


class MagentoProductType(ModelSQL, ModelView):
    'Magento Product Type'
    __name__ = 'magento.product.type'
    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True,
        help='Same name Magento product type, (example: simple)')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


class MagentoAttributeConfigurable(ModelSQL, ModelView):
    'Magento Attribute Configurable'
    __name__ = 'magento.attribute.configurable'
    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True)
    mgn_id = fields.Char('Mgn ID', required=True,
        help='Magento ID')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


class Template:
    __name__ = 'product.template'
    magento_product_type = fields.Selection('get_magento_product_type', 'Product Type',
        states={
            'required': Eval('esale_available', True),
        },
        depends=['esale_available'])
    magento_group_price = fields.Boolean('Magento Grup Price',
        help='If check this value, when export product prices (and shop '
            'is active group price), export prices by group')
    magento_attribute_configurable = fields.Many2One('magento.attribute.configurable',
        'Configurable Attribute', states={
            'invisible': ~(Eval('magento_product_type') == 'configurable'),
            'required': Eval('magento_product_type') == 'configurable',
            },
        depends=['magento_product_type'])

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        # Add base code require attribute
        for fname in ('base_code',):
            fstates = getattr(cls, fname).states
            if fstates.get('required'):
                fstates['required'] = Or(fstates['required'],
                    Eval('magento_product_type', '=', 'configurable'))
            else:
                fstates['required'] = Eval('magento_product_type') == 'configurable'
            getattr(cls, fname).depends.append('magento_product_type')

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


class Product:
    __name__ = 'product.product'

    @classmethod
    def magento_template_dict2vals(self, shop, values):
        vals = super(Product, self).magento_template_dict2vals(shop, values)
        vals['esale_available'] = True
        vals['esale_active'] = True
        vals['esale_shortdescription'] = values.get('short_description')
        vals['esale_slug'] = values.get('url_key')
        return vals

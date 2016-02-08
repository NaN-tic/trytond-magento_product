# This file is part magento_product module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from wikimarkup import parse as wiki_parse
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Not, Equal, Or
from trytond.transaction import Transaction
from trytond import backend

__all__ = ['MagentoProductType', 'MagentoAttributeConfigurable',
    'TemplateMagentoAttributeConfigurable', 'Template', 'Product']
__metaclass__ = PoolMeta

_MAGENTO_VISIBILITY = {
    'none': '1',
    'catalog': '2',
    'search': '3',
    'all': '4',
    }

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
    app = fields.Many2One('magento.app', 'APP', required=True)
    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True)
    mgn_id = fields.Char('Mgn ID', required=True,
        help='Magento ID')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_app():
        App = Pool().get('magento.app')
        apps = App.search([])
        if len(apps) == 1:
            return apps[0].id


class TemplateMagentoAttributeConfigurable(ModelSQL):
    'Product Template - Magento Attribute Configurable'
    __name__ = 'product.template-magento.attribute.configurable'
    _table = 'product_tpl_mgn_attribute_configurable'
    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            required=True, select=True)
    configurable = fields.Many2One('magento.attribute.configurable', 'Attribute Configurable',
        ondelete='CASCADE', required=True, select=True)

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().cursor

        # Migration from 3.6: rename table
        old_table = 'product_template_magento_attribute_configurable_rel'
        new_table = 'product_tpl_mgn_attribute_configurable'
        if TableHandler.table_exist(cursor, old_table):
            TableHandler.table_rename(cursor, old_table, new_table)

        super(TemplateMagentoAttributeConfigurable, cls).__register__(module_name)


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
    magento_attribute_configurables = fields.Many2Many('product.template-magento.attribute.configurable',
        'template', 'configurable', 'Configurable Attribute', states={
            'invisible': ~(Eval('magento_product_type') == 'configurable'),
            'required': Eval('magento_product_type') == 'configurable',
            },
        depends=['magento_product_type'],
        help='Add attributes before export configurable product')

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
    def view_attributes(cls):
        return super(Template, cls).view_attributes() + [
            ('//page[@id="magento-attribute-configurables"]', 'states', {
                    'invisible': Not(Equal(Eval('magento_product_type'), 'configurable')),
                    })]

    @classmethod
    def get_magento_product_type(cls):
        ProductType = Pool().get('magento.product.type')

        types = [(None, '')]
        records = ProductType.search([
            ('active', '=', True),
            ], order=[('id', 'DESC')])
        if not records:
            return types
        product_types = ProductType.read(records, ['code', 'name'])
        if product_types:
            for pt in product_types:
                types.append((pt['code'], pt['name']))
        return types

    @staticmethod
    def default_magento_product_type():
        product_type = None
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
    def magento_import_product(cls, values, shop=None):
        '''Magento Import Product values'''
        vals = super(Product, cls).magento_import_product(values, shop)

        visibility = values.get('visibility')
        if visibility == '1':
            visibility = 'none'
        elif visibility == '2':
            visibility = 'catalog'
        elif visibility == '3':
            visibility = 'search'
        else:
            visibility = 'all'

        status = values.get('status', '1')
        if status == '1':
            esale_available = True
        else:
            esale_available = False

        vals['esale_available'] = True
        vals['esale_active'] = True
        vals['esale_shortdescription'] = values.get('short_description')
        vals['esale_slug'] = values.get('url_key')
        vals['magento_product_type'] = values.get('type_id')
        vals['special_price'] = values.get('special_price')
        vals['special_price_from'] = values.get('special_from_date')
        vals['special_price_to'] = values.get('special_to_date')
        vals['template_attributes'] = {'tax_class_id': values.get('tax_class_id', '0')}
        vals['esale_visibility'] = visibility
        vals['esale_attribute_group'] = 1 # ID default attribute
        vals['esale_available'] = esale_available
        vals['esale_shortdescription'] = values.get('short_description')
        vals['esale_metadescription'] = values.get('meta_description')
        vals['esale_metakeyword'] = values.get('meta_keyword')
        vals['esale_metatitle'] = values.get('meta_title')
        vals['esale_description'] = values.get('description')
        return vals

    @classmethod
    def magento_export_product(cls, app, product, shop=None, lang='en_US'):
        '''Magento Export Product values'''
        pool = Pool()
        MagentoExternalReferential = pool.get('magento.external.referential')
        Product = pool.get('product.product')

        language = Transaction().context.get('language')

        if language != lang:
            with Transaction().set_context(language=lang):
                product = Product(product.id)

        vals = {}
        vals['name'] = product.name
        vals['sku'] = product.code
        vals['type_id'] = product.magento_product_type
        vals['url_key'] = product.esale_slug
        vals['cost'] = str(product.cost_price)
        vals['price'] = str(product.list_price)
        vals['special_price'] = product.special_price
        vals['special_from_date'] = product.special_price_from
        vals['special_to_date'] = product.special_price_to
        vals['tax_class_id'] = product.attributes.get('tax_class_id') if product.attributes else None
        vals['visibility'] = _MAGENTO_VISIBILITY.get(product.esale_visibility, '4')
        vals['set'] = '4' #ID default attribute
        vals['status'] = '1' if product.esale_active else '2'
        vals['short_description'] = wiki_parse(product.esale_shortdescription)
        vals['meta_description'] = product.esale_metadescription
        vals['meta_keyword'] = product.esale_metakeyword
        vals['meta_title'] = product.esale_metatitle
        vals['description'] = wiki_parse(product.esale_description)

        vals['categories'] = [menu.magento_id for menu in product.esale_menus if menu.magento_app == app]

        websites = []
        for shop in product.shops:
            ext_ref = MagentoExternalReferential.get_try2mgn(app,
                    'magento.website',
                    shop.magento_website.id)
            if ext_ref:
                websites.append(ext_ref.mgn_id)
        vals['websites'] = websites
        return vals

    @classmethod
    def magento_export_product_configurable(cls, app, template, shop=None, lang='en_US'):
        '''Magento Export Configurable Product values (template)'''
        pool = Pool()
        MagentoExternalReferential = pool.get('magento.external.referential')
        Template = pool.get('product.template')

        language = Transaction().context.get('language')

        if language != lang:
            with Transaction().set_context(language=lang):
                template = Template(template.id)

        vals = {}
        vals['name'] = template.name
        vals['sku'] = template.code
        vals['url_key'] = template.esale_slug
        vals['cost'] = str(template.cost_price)
        vals['price'] = str(template.list_price)
        vals['special_price'] = template.special_price
        vals['special_from_date'] = template.special_price_from
        vals['special_to_date'] = template.special_price_to
        vals['tax_class_id'] = template.attributes.get('tax_class_id') if template.attributes else None
        vals['visibility'] = _MAGENTO_VISIBILITY.get(template.esale_visibility, '4')
        vals['set'] = '4' #ID default attribute
        vals['status'] = '1' if template.esale_active else '2'
        vals['short_description'] = wiki_parse(template.esale_shortdescription)
        vals['meta_description'] = template.esale_metadescription
        vals['meta_keyword'] = template.esale_metakeyword
        vals['meta_title'] = template.esale_metatitle
        vals['description'] = wiki_parse(template.esale_description)

        vals['categories'] = [menu.magento_id for menu in template.esale_menus if menu.magento_app == app]

        websites = []
        for shop in template.shops:
            ext_ref = MagentoExternalReferential.get_try2mgn(app,
                    'magento.website',
                    shop.magento_website.id)
            if ext_ref:
                websites.append(ext_ref.mgn_id)
        vals['websites'] = websites
        return vals

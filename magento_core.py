# This file is part magento_manufacturer module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.modules.product_esale.tools import slugify, seo_lenght
from wikimarkup import parse as wikihtml

from magento import *
import logging
import urllib

__all__ = ['MagentoApp', 'MagentoSaleShopGroupPrice']
__metaclass__ = PoolMeta

_ATTRIBUTE_OPTIONS_TYPE = ['select']


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
    catalog_price = fields.Selection([
            ('global','Global'),
            ('website','Website'),
            ],
        'Catalog Price', help='Magento Configuration/Catalog/Price/Catalog '
            'Price Scope')
    top_menu = fields.Many2One('esale.catalog.menu', 'Top Menu')

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
                'select_top_menu': 'Select Top Menu Category!',
                'magento_api_error': 'Magento API Error!',
                'shop_not_found': 'Shop not found.',
                'shop_without_default_uom': 'Shop has not any default uom.'
                })
        cls._buttons.update({
                'core_import_product_type': {},
                'core_import_group_attributes': {},
                'core_import_attributes_options': {},
                'core_import_categories': {},
                'core_import_products': {},
                'core_import_product_links': {},
                'core_export_categories': {},
                })

    @staticmethod
    def default_catalog_price():
        return 'global'

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
                        external_id,
                        ))

    @classmethod
    @ModelView.button
    def core_import_attributes_options(self, apps):
        """Import Magento Attribute Options to Tryton
        """
        pool = Pool()
        Attribute = pool.get('product.attribute')
        AttrGroup = pool.get('esale.attribute.group')
        ExternalReferential = pool.get('magento.external.referential')

        for app in apps:
            groups = AttrGroup.search([])
            for group in groups:
                attr_external = ExternalReferential.get_try2mgn(app,
                        'esale.attribute.group', group.id)
                if attr_external:
                    with ProductAttribute(app.uri, app.username, app.password) as \
                            product_attribute_api:
                        attributes = product_attribute_api.list(attr_external.mgn_id)

                        for attribute in attributes:
                            if attribute.get('type') not in _ATTRIBUTE_OPTIONS_TYPE:
                                continue
                            attrs = Attribute.search([
                                ('name', '=', attribute.get('code'))
                                ], limit=1)
                            if not attrs:
                                continue

                            attr, = attrs
                            if attribute.get('type') == 'select':
                                options = product_attribute_api.options(attr.name)
                                opt = []
                                for option in options:
                                    if not option.get('value'):
                                        continue
                                    opt.append('%s:%s' % (
                                            option.get('value'),
                                            option.get('label'),
                                            ))
                                if opt:
                                    Attribute.write([attr], {
                                        'selection': '\n'.join(opt),
                                        })
                                    logging.getLogger('magento').info(
                                        'Save attribute options %s' % (attr.name))

        logging.getLogger('magento').info('End import attribute options')

    def save_menu(self, data, parent=None, menu=None):
        '''
        Save Menu
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
        metadescription = seo_lenght(data.get('meta_description')) if data.get('meta_description') else None
        metakeyword = seo_lenght(data.get('meta_keywords')) if data.get('meta_keywords') else None
        metatitle = seo_lenght(data.get('meta_title')) if data.get('meta_title') else None

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
        menu.magento_app = self.id
        menu.magento_id = data.get('category_id')
        menu.save()

        logging.getLogger('magento').info(
            '%s category %s (%s)' % (action.capitalize(), menu.name, menu.id))
        return menu

    @classmethod
    def save_menu_language(self, menu, data, language='en_US'):
        '''
        Save menu by language
        :param menu: object
        :param data: dict
        :param language: code language
        :return: object
        '''
        Menu = Pool().get('esale.catalog.menu')

        metadescription = seo_lenght(data.get('meta_description')) if data.get('meta_description') else None
        metakeyword = seo_lenght(data.get('meta_keywords')) if data.get('meta_keywords') else None
        metatitle = seo_lenght(data.get('meta_title')) if data.get('meta_title') else None

        vals = {}
        vals['name'] = data.get('name')
        if data.get('url_key'):
            vals['slug'] = data.get('url_key')
        if data.get('description'):
            vals['description'] = data.get('description')
        if metadescription:
            vals['metadescription'] = metadescription
        if metakeyword:
            vals['metakeyword'] = metakeyword
        if metatitle:
            vals['metatitle'] = metatitle

        with Transaction().set_context(language=language):
            Menu.write([menu], vals)
        logging.getLogger('magento').info(
            'Update category %s (%s-%s)' % (data.get('name'), menu.id, language))
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
                with Transaction().set_context(active_test=False):
                    menus = Menu.search([
                            ('magento_app', '=', app.id),
                            ('magento_id', '=', children.get('category_id')),
                            ], limit=1)

                cat_info = category_api.info(children.get('category_id'))
                if menus:
                    menu, = menus
                    app.save_menu(cat_info, parent, menu)
                if not menus:
                    menu = app.save_menu(cat_info, parent)

                # save categories by language
                for lang in app.languages:
                    cat_info = category_api.info(cat_info.get('category_id'), store_view=lang.storeview.code)
                    language = 'en_US' if lang.default else lang.lang.code #use default language to en_US
                    self.save_menu_language(menu, cat_info, language=language)

                if children.get('children'):
                    data = category_api.tree(parent_id=children.get('category_id'))
                    self.children_categories(app, menu.id, data)

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

                with Transaction().set_context(active_test=False):
                    category_roots = Menu.search([
                        ('magento_app', '=', app.id),
                        ('magento_id', '=', data.get('category_id')),
                        ], limit=1)

                if not category_roots:
                    root_info = category_api.info(data.get('category_id'))
                    category_root = app.save_menu(root_info)
                    category_root.active = True
                    category_root.save()
                else:
                    category_root, = category_roots

                Transaction().cursor.commit()
                self.children_categories(app, category_root.id, data)

            logging.getLogger('magento').info(
                'End import categories %s' % (app.name))

    @classmethod
    def magento_category_values(self, menu):
        '''Return Magento Values from Menu
        :param menu: object
        return dict
        '''
        sort_by = menu.default_sort_by
        if sort_by == '':
            sort_by = 'name'

        data = {}
        data['name'] = menu.name
        data['is_active'] = '1' if menu.active else '0'
        data['available_sort_by'] = sort_by
        data['default_sort_by'] = sort_by
        data['description'] = wikihtml(menu.description)
        data['metadescription'] = menu.metadescription
        data['metakeyword'] = menu.metakeyword
        data['metatitle'] = menu.metatitle
        data['url_key'] = menu.slug
        data['include_in_menu'] = '1' if menu.include_in_menu else '0'
        return data

    @classmethod
    @ModelView.button
    def core_export_categories(self, apps):
        """Export Magento Categories to Tryton
        Only create/update categories; not delete
        """
        Menu = Pool().get('esale.catalog.menu')

        for app in apps:
            logging.getLogger('magento').info(
                'Start export categories %s' % (app.name))
            if not app.top_menu:
                self.raise_user_error('select_top_menu')
            if not app.magento_default_storeview:
                self.raise_user_error('select_store_view')

            top_menu = app.top_menu
            store_view = app.magento_default_storeview.code

            menus = Menu.get_allchild(top_menu)

            with Category(app.uri, app.username, app.password) as category_api:
                for menu in menus:
                    magento_id = menu.magento_id

                    data = self.magento_category_values(menu)

                    if app.debug:
                        message = 'Magento %s. Category: %s' % (
                                app.name, data)
                        logging.getLogger('magento').info(message)

                    try:
                        if magento_id:
                            action = 'update'
                            category_api.update(magento_id, data)
                        else:
                            action = 'create'
                            parent_id = menu.parent.magento_id
                            mgn_cat = category_api.create(parent_id, data, store_view)
                            Menu.write([menu], {
                                    'magento_id': mgn_cat,
                                    'magento_app': app.id,
                                    })

                        message = 'Magento %s. %s category: %s (%s)' % (
                                app.name, action.capitalize(), menu.name, menu.id)
                        logging.getLogger('magento').info(message)
                    except Exception, e:
                        message = 'Magento %s. Error export category ID %s: %s' % (
                                    app.name, menu.id, e)
                        logging.getLogger('magento').error(message)

                    Transaction().cursor.commit()

                    # Export categories by languages
                    for lang in app.languages:
                        language = lang.lang.code
                        with Transaction().set_context(language=language):
                            menu_lang = Menu(menu)
                            data = self.magento_category_values(menu_lang)

                        try:
                            magento_id = menu_lang.magento_id
                            sview = lang.storeview.code
                            
                            category_api.update(magento_id, data, sview)
                            message = 'Magento %s. Update category: %s (%s)' % (
                                    app.name, menu.name, language)
                            logging.getLogger('magento').info(message)
                        except Exception, e:
                            message = 'Magento %s. Error export category lang ID %s: %s' % (
                                        app.name, menu.id, e)
                            logging.getLogger('magento').error(message)

            logging.getLogger('magento').info(
                'End import categories %s' % (app.name))

    @classmethod
    def save_product(self, app, data, product=None):
        '''
        Save Product
        :param app: object
        :param data: dict
        :param product: object
        :return: object
        '''
        pool = Pool()
        ProductProduct = pool.get('product.product')
        ProductTemplate = pool.get('product.template')
        BaseExternalMapping = pool.get('base.external.mapping')
        Menu = pool.get('esale.catalog.menu')
        Shop = pool.get('sale.shop')

        template_mapping = app.template_mapping.name
        product_mapping = app.product_mapping.name

        # get default values
        tvals = ProductTemplate.esale_template_values()
        pvals = ProductProduct.esale_product_values()

        # get values using base external mapping
        tvals.update(BaseExternalMapping.map_external_to_tryton(template_mapping, data))
        pvals.update(BaseExternalMapping.map_external_to_tryton(product_mapping, data))

        # Shops - websites
        shops = ProductProduct.magento_product_esale_saleshops(app, data)
        if not shops:
            self.raise_user_error('shop_not_found')
        shop = Shop(shops[0])
        if shop.esale_uom_product:
            default_uom = shop.esale_uom_product
        else:
            self.raise_user_error('shop_without_default_uom')

        if shops:
            tvals['esale_saleshops'] = shops

        # Categories -> menus
        menus = Menu.search([
                ('magento_app', '=', app.id),
                ('magento_id', 'in', data.get('categories')),
                ])
        if menus:
            tvals['esale_menus'] = [menu.id for menu in menus]

        if app.debug:
            logging.getLogger('magento').info(
                'Product values: %s' % (dict(tvals.items() + pvals.items())))

        if not product:
            template = ProductTemplate()
            product = ProductProduct()
            action = 'create'

            # Taxes and list price and cost price with or without taxes
            tax_include = app.tax_include
            customer_taxes, list_price, cost_price = ProductProduct.magento_product_esale_taxes(app, data, tax_include)
            if customer_taxes:
                tvals['customer_taxes'] = customer_taxes
            if not list_price:
                list_price = data.get('price')
            tvals['list_price'] = list_price
            if not cost_price:
                cost_price = data.get('price')
            tvals['cost_price'] = cost_price

            tvals['default_uom'] = default_uom
            tvals['sale_uom'] = default_uom
            tvals['category'] = shop.esale_category
        else:
            template = product.template
            action = 'update'
            if tvals.get('type'):
                del tvals['type']

        for key, value in tvals.iteritems():
            setattr(template, key, value)

        for key, value in pvals.iteritems():
            setattr(product, key, value)

        template.products = [product]
        template.save()

        logging.getLogger('magento').info(
            '%s product %s (%s)' % (action.capitalize(), template.rec_name, template.id))

        return template

    @classmethod
    def save_product_language(self, app, template, data, language='en_US'):
        '''
        Save product by language
        :param app: object
        :param template: object
        :param data: dict
        :param language: code language
        :return: object
        '''
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')

        BaseExternalMapping = pool.get('base.external.mapping')

        template_mapping = app.template_mapping.name
        product_mapping = app.product_mapping.name

        # get values using base external mapping
        tmp_vals = BaseExternalMapping.map_external_to_tryton(template_mapping, data)
        tvals = BaseExternalMapping.map_exclude_update(template_mapping, tmp_vals)
        prod_vals = BaseExternalMapping.map_external_to_tryton(product_mapping, data)
        pvals = BaseExternalMapping.map_exclude_update(product_mapping, prod_vals)

        tmpl_vals = {}
        for key, value in tvals.iteritems():
            tmpl_vals[key] = value

        prod_vals = {}
        for key, value in pvals.iteritems():
            prod_vals[key] = value

        with Transaction().set_context(language=language):
            Template.write([template], tmpl_vals)
            logging.getLogger('magento').info(
                'Update template %s (%s-%s)' % (data.get('name'), template.id, language))
            for product in template.products:
                if product.code == pvals.get('code'):
                    Product.write([product], prod_vals)
                    logging.getLogger('magento').info(
                        'Update product %s (%s-%s)' % (data.get('name'), product.id, language))

        return template

    @classmethod
    def save_product_images(self, app, template, code):
        '''
        Save product images
        :param app: object
        :param template: object
        :param code: str
        '''
        pool = Pool()
        Attachment = pool.get('ir.attachment')
        
        with ProductImages(app.uri, app.username, app.password) as product_images_api:
            for image in product_images_api.list(code):

                if 'url' in image: # magento = 1.3
                    url = image.get('url')
                else: # magento > 1.4
                    url = image.get('filename')
                if not url:
                    continue
                name = url.split('/')[-1:][0]
                attachments = Attachment.search([
                    ('name', '=', name),
                    ('resource', '=', '%s' % (template)),
                    ], limit=1)
                if attachments:
                    action = 'update'
                    attachment, = attachments
                else:
                    action = 'create'
                    attachment = Attachment()

                exclude = False
                if image.get('exclude') == '1':
                    exclude = True
                
                base_image = False
                small_image = False
                thumbnail = False
                if 'image' in image.get('types'):
                    base_image = True
                if 'small_image' in image.get('types'):
                    small_image = True
                if 'thumbnail' in image.get('types'):
                    thumbnail = True

                attachment.name = name
                attachment.type = 'data'
                attachment.data = urllib.urlopen(url).read()
                attachment.resource = '%s' % (template)
                attachment.description = image.get('label')
                attachment.esale_available = True
                attachment.esale_base_image = base_image
                attachment.esale_small_image = small_image
                attachment.esale_thumbnail = thumbnail
                attachment.esale_exclude = exclude
                attachment.esale_position = image.get('position')
                attachment.save()

                logging.getLogger('magento').info(
                    '%s image %s (%s)' % (action.capitalize(), name, attachment.id))

    @classmethod
    @ModelView.button
    def core_import_products(self, apps):
        """Import Magento Products to Tryton
        Create/Update new products; not delete
        """
        pool = Pool()
        ProductProduct = pool.get('product.product')

        for app in apps:
            if not app.magento_websites:
                self.raise_user_error('import_magento_website')

            if not app.magento_websites or not app.product_mapping:
                self.raise_user_error('select_mapping')

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
                    products_created = product_api.list(ofilter)
                    products_updated = products+product_api.list(ofilter2)
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
                    products = product_api.list(ofilter)
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

                    with Transaction().set_context(active_test=False):
                        prods = ProductProduct.search([
                            ('code', '=', product.get('sku')),
                            ], limit=1)
                    if prods:
                        prod, = prods
                    else:
                        prod = None

                    #save product data
                    product_info = product_api.info(code)
                    template = self.save_product(app, product_info, prod)

                    # save products by language
                    for lang in app.languages:
                        product_info = product_api.info(code, store_view=lang.storeview.code)
                        language = 'en_US' if lang.default else lang.lang.code #use default language to en_US
                        self.save_product_language(app, template, product_info, language)

                    # save images products
                    self.save_product_images(app, template, code)

                    Transaction().cursor.commit()

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


class MagentoSaleShopGroupPrice(ModelSQL, ModelView):
    'Magento Sale Shop Group Price'
    __name__ = 'magento.sale.shop.group.price'
    shop = fields.Many2One('sale.shop', 'Shop', required=True)
    group = fields.Many2One('magento.customer.group', 'Customer Group', required=True)
    price_list = fields.Many2One('product.price_list', 'Pricelist', required=True)

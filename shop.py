# This file is part magento_product module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, Not, Equal
from mimetypes import guess_type
from magento import *
import datetime
import logging
import base64

__all__ = ['SaleShop']
__metaclass__ = PoolMeta

_MIME_TYPES = ['image/jpeg', 'image/png']
logger = logging.getLogger(__name__)


class SaleShop:
    __name__ = 'sale.shop'
    magento_group_price = fields.Boolean('Magento Grup Price',
        help='If check this value, when export product prices add prices by group')
    magento_shop_group_prices = fields.One2Many('magento.sale.shop.group.price', 'shop',
        'Magento Shop Grup Price')

    @classmethod
    def __setup__(cls):
        super(SaleShop, cls).__setup__()
        cls._error_messages.update({
            'export_menus': 'Use Magento APP to export menus (categories).',
        })

    @classmethod
    def view_attributes(cls):
        return super(SaleShop, cls).view_attributes() + [
            ('//page[@id="magento-product"]', 'states', {
                    'invisible': Not(Equal(Eval('esale_shop_app'), 'magento')),
                    })]

    def magento_get_prices(self, product, quantity=1):
        """
        Get Products Price, Sepcial Price and Group price
        from price list or price (with or not taxes)
        :param product: object
        :param quantity: int
        :return dicc
        """
        pool = Pool()
        Product = pool.get('product.product')

        # Sale Price
        price = 0
        if self.esale_price == 'pricelist' and self.price_list and self.esale_price_party:
            context = {
                'price_list': self.price_list.id,
                'customer': self.esale_price_party.id,
                'without_special_price': True,
                }
            with Transaction().set_context(context):
                prices = Product.get_sale_price([product], quantity)
                price = prices[product.id]
        else:
            price = product.template.list_price

        if self.esale_tax_include:
            price = self.esale_price_w_taxes(product, price, quantity)

        # Special Price
        special_price = ''
        shop_special_price = False
        if hasattr(self, 'special_price'):
            shop_special_price = True
        if shop_special_price and self.special_price:
            if self.type_special_price == 'pricelist':
                context = {
                    'price_list': self.price_list.id,
                    'customer': self.esale_price_party.id,
                    }
                with Transaction().set_context(context):
                    special_prices = Product.get_sale_price([product],
                        quantity)
                    special_price = special_prices[product.id]
            else:
                special_price = product.template.special_price or 0

            if self.esale_tax_include:
                special_price = self.esale_price_w_taxes(product, special_price, quantity)

            if not (special_price > 0.0 and special_price < price):
                special_price = ''

        # Group Price
        group_price = []
        if self.magento_shop_group_prices and product.magento_group_price:
            # {'cust_group': '0', 'website_price': '10.0000', 'price': '10.0000', 
            # 'website_id': '0', 'price_id': '1', 'all_groups': '0'}
            for group_prices in self.magento_shop_group_prices:
                context = {
                    'price_list': group_prices.price_list.id,
                    'customer': self.esale_price_party.id,
                    'without_special_price': True,
                    }
                with Transaction().set_context(context):
                    gprices = Product.get_sale_price([product],
                        quantity)
                    gprice = gprices[product.id]
                if gprice > 0.0:
                    if self.esale_tax_include:
                        gprice = self.esale_price_w_taxes(product, gprice, quantity)
                    group_price.append({
                        'cust_group': group_prices.group.customer_group,
                        'price': str(gprice),
                        })

        data = {}
        data['price'] = str(price)
        if shop_special_price:
            data['special_price'] = str(special_price)
            if shop_special_price:
                data['special_from_date'] = product.special_price_from.strftime("%Y-%m-%d %H:%M:%S") if product.special_price_from else ''
                data['special_to_date'] = product.special_price_to.strftime("%Y-%m-%d %H:%M:%S") if product.special_price_to else ''
        data['group_price'] = group_price
        return data

    def export_products_magento(self, tpls=[]):
        """Export Products to Magento
        :param tpls: list
        """
        pool = Pool()
        Prod = pool.get('product.product')
        MagentoExternalReferential = pool.get('magento.external.referential')
        BaseExternalMapping = pool.get('base.external.mapping')

        product_domain = Prod.magento_product_domain([self.id])

        context = Transaction().context

        if tpls:
            product_domain += [('template.id', 'in', tpls)]
        else:
            now = datetime.datetime.now()
            last_products = self.esale_last_products

            product_domain += [['OR',
                        ('create_date', '>=', last_products),
                        ('write_date', '>=', last_products),
                        ('template.create_date', '>=', last_products),
                        ('template.write_date', '>=', last_products),
                    ]]

            # Update date last import
            self.write([self], {'esale_last_products': now})
            Transaction().cursor.commit()

        products = Prod.search(product_domain)
        templates = list(set(p.template for p in products))

        if not templates:
            logger.info(
                'Magento %s. Not products to export.' % (self.name))
            return

        logger.info(
            'Magento %s. Start export %s product(s).' % (
                self.name, len(templates)))

        app = self.magento_website.magento_app

        language = context.get('language')
        default_storeview = app.magento_default_storeview
        if default_storeview:
            for l in app.languages:
                if l.storeview.id == default_storeview.id:
                    language = l.lang.code
                    break

        with Product(app.uri, app.username, app.password) as product_api:
            for template in templates:
                product_type = template.magento_product_type

                if not template.esale_attribute_group:
                    message = 'Magento %s. Error export template ID %s. ' \
                            'Select eSale Attribute' % (self.name, template.id)
                    logger.error(message)
                    continue

                total_products = len(template.products)

                for product in template.products:
                    if not product.code:
                        message = 'Magento %s. Error export product ID %s. ' \
                                'Add a code' % (self.name, product.id)
                        logger.error(message)
                        continue

                    code = product.code
                    values = Prod.magento_export_product(app, product, shop=self, lang=language)
                    prices = self.magento_get_prices(product)
                    values.update(prices)
                    
                    if not values.get('tax_class_id'):
                        for tax in app.magento_taxes:
                            values['tax_class_id'] = tax.tax_id
                            break
                    if product_type == 'configurable':
                        # force visibility Not Visible Individually
                        values['visibility'] = '1'
                        # product name from product_name module if installed
                        values['name'] = product.name if product.name else product.template.name
                        # each variant add attribute options in product name
                    if product_type == 'grouped':
                        # force visibility Not Visible Individually
                        values['visibility'] = '1'

                    # if products > 1, add code prefix in url key
                    if total_products > 1:
                        url_key = values.get('url_key')
                        values['url_key'] = '%s-%s' % (code.lower(), url_key)

                    if app.debug:
                        message = 'Magento %s. Product: %s. Values: %s' % (
                                self.name, code, values)
                        logger.info(message)

                    mgn_prods = product_api.list({'sku': {'=': code}})

                    try:
                        if mgn_prods:
                            action = 'update'
                            product_api.update(code, values, identifierType=app.identifier_type)
                        else:
                            action = 'create'
                            del values['sku']

                            # Product type
                            if product_type == 'configurable':
                                magento_product_type = 'simple'
                            else:
                                magento_product_type = product.template.magento_product_type
                                
                            ext_ref = MagentoExternalReferential.get_try2mgn(app,
                                    'esale.attribute.group',
                                    template.esale_attribute_group.id)
                            attribute_mgn = ext_ref.mgn_id

                            mgn_id = product_api.create(magento_product_type, attribute_mgn, code, values)

                            message = 'Magento %s. %s product %s. Magento ID %s' % (
                                    self.name, action.capitalize(), code, mgn_id)
                            logger.info(message)
                    except Exception, e:
                        action = None
                        message = 'Magento %s. Error export product %s: %s' % (
                                    self.name, code, e)
                        logger.error(message)

                    if not action:
                        continue

                    # save products by language
                    for l in app.languages:
                        values = Prod.magento_export_product(app, product, lang=l.lang.code)

                        if product_type in ['configurable', 'grouped']:
                            # force visibility Not Visible Individually
                            values['visibility'] = '1'
                            if values.get('description'):
                                values['name'] = values['description']

                        if app.debug:
                            message = 'Magento %s. Product: %s. Values: %s' % (
                                    self.name, code, values)
                            logger.info(message)

                        product_api.update(code, values, l.storeview.code, identifierType=app.identifier_type)

                        message = 'Magento %s. Update product %s (%s)' % (
                                self.name, code, l.lang.code)
                        logger.info(message)

                # ===========================
                # Export Configurable Product
                # ===========================
                if product_type == 'configurable':
                    if not template.base_code:
                        logger.warning('Product Template not have base code')
                        continue

                    if not template.products:
                        logger.warning('Template not have products')
                        continue
                    values = Prod.magento_export_product_configurable(app, template, shop=self, lang=language)
                    prices = self.magento_get_prices(template.products[0])
                    values.update(prices)

                    mgn_prods = product_api.list({'sku': {'=': code}})
                    
                    try:
                        if mgn_prods:
                            action = 'update'
                            product_api.update(code, values, identifierType=app.identifier_type)
                        else:
                            action = 'create'

                            magento_product_type = template.magento_product_type

                            ext_ref = MagentoExternalReferential.get_try2mgn(app,
                                    'esale.attribute.group',
                                    template.esale_attribute_group.id)
                            attribute_mgn = ext_ref.mgn_id

                            mgn_id = product_api.create(magento_product_type, attribute_mgn, code, values)

                            # set attribute product configuration
                            with ProductConfigurable(app.uri, app.username, app.password) as product_conf_api:
                                # assign each magento attribute
                                for attribute in template.magento_attribute_configurables:
                                    product_conf_api.setSuperAttributeValues(mgn_id, attribute.mgn_id)

                            message = 'Magento %s. %s product %s. Magento ID %s' % (
                                    self.name, action.capitalize(), code, mgn_id)
                            logger.info(message)
                    except Exception, e:
                        message = 'Magento %s. Error export product %s: %s' % (
                                    self.name, code, e)
                        logger.error(message)
                        continue

                    # Relate product simple to product configuration
                    ofilter = {'sku': {'in': ['%s' % p.code for p in template.products]}}
                    products = product_api.list(ofilter)
                    with ProductConfigurable(app.uri, app.username, app.password) as product_conf_api:
                        try:
                            simples = [p['product_id'] for p in products]
                            product_conf_api.update(code, simples, {})
                            message = 'Magento %s. Update %s with configurable %s' % (
                                    self.name, code, simples)
                            logger.info(message)
                        except Exception, e:
                            action = None
                            message = 'Magento %s. Error export product %s: %s' % (
                                        self.name, code, e)
                            logger.error(message)

                    # save products by language
                    for lang in app.languages:
                        with Transaction().set_context(language=lang.lang.code):
                            product = Prod(product.id)
                            tvals, = BaseExternalMapping.map_tryton_to_external(template_mapping, [product.template.id])
                        values = tvals

                        if app.debug:
                            message = 'Magento %s. Product: %s. Values: %s' % (
                                    self.name, code, values)
                            logger.info(message)

                        product_api.update(code, values, lang.storeview.code, identifierType=app.identifier_type)

                        message = 'Magento %s. Update product %s (%s)' % (
                                self.name, code, lang.lang.code)
                        logger.info(message)
                    # END product configuration

        logger.info(
            'Magento %s. End export %s product(s).' % (
                self.name, len(templates)))

        # =====================
        # Export Stock + Images
        # =====================
        if hasattr(self, 'export_stocks_magento'):
            self.export_stocks_magento([t.id for t in templates]) # Export Inventory - Stock
        self.export_images_magento([t.id for t in templates]) # Export Images
        #TODO: Export Product Links

    def export_prices_magento(self, tpls=[]):
        """Export Prices to Magento
        :param shop: object
        :param tpls: list
        """
        pool = Pool()
        Prod = pool.get('product.product')
        MagentoExternalReferential = pool.get('magento.external.referential')

        product_domain = Prod.magento_product_domain([self.id])

        if tpls:
            product_domain += [('template.id', 'in', tpls)]
        else:
            now = datetime.datetime.now()
            last_prices = self.esale_last_prices

            product_domain += [['OR',
                        ('create_date', '>=', last_prices),
                        ('write_date', '>=', last_prices),
                        ('template.create_date', '>=', last_prices),
                        ('template.write_date', '>=', last_prices),
                    ]]

            # Update date last import
            self.write([self], {'esale_last_prices': now})
            Transaction().cursor.commit()

        products = Prod.search(product_domain)

        if not products:
            logger.info(
                'Magento %s. Not products to export prices.' % (self.name))
            return

        logger.info(
            'Magento %s. Start export prices. %s product(s).' % (
                self.name, len(products)))

        app = self.magento_website.magento_app

        with Product(app.uri, app.username, app.password) as product_api:
            for product in products:
                if not product.code:
                    continue
                code = product.code

                data = self.magento_get_prices(product)

                if app.debug:
                    message = 'Magento %s. Product: %s. Data: %s' % (
                            self.name, code, data)
                    logger.info(message)

                try:
                    if app.catalog_price == 'website':
                        ext_ref = MagentoExternalReferential.get_try2mgn(app,
                                'magento.external.referential',
                                self.magento_website.id)
                        magento_website = ext_ref.mgn_id
                        product_api.update(code, data, magento_website, identifierType=app.identifier_type)
                        if self.magento_price_global: # Global price
                            product_api.update(code, data, identifierType=app.identifier_type) 
                    else:
                        product_api.update(code, data, identifierType=app.identifier_type)

                    message = 'Magento %s. Export price %s product.' % (
                            self.name, code)
                    logger.info(message)
                except Exception, e:
                    message = 'Magento %s. Error export prices to product %s: %s' % (
                                self.name, code, e)
                    logger.error(message)

        logger.info(
            'Magento %s. End export prices %s products.' % (
                self.name, len(products)))

    def export_images_magento(self, tpls=[]):
        """Export Images to Magento
        :param shop: object
        :param tpls: list
        """
        Prod = Pool().get('product.product')

        product_domain = Prod.magento_product_domain([self.id])

        if tpls:
            product_domain += [('template.id', 'in', tpls)]
        else:
            now = datetime.datetime.now()
            last_images = self.esale_last_images

            product_domain += [['OR',
                        ('create_date', '>=', last_images),
                        ('write_date', '>=', last_images),
                        ('template.create_date', '>=', last_images),
                        ('template.write_date', '>=', last_images),
                    ]]

            # Update date last import
            self.write([self], {'esale_last_images': now})
            Transaction().cursor.commit()

        products = Prod.search(product_domain)
        templates = list(set(p.template for p in products))

        if not templates:
            logger.info(
                'Magento %s. Not product images to export.' % (self.name))
            return

        logger.info(
            'Magento %s. Start export images. %s product(s).' % (
                self.name, len(templates)))

        app = self.magento_website.magento_app

        for template in templates:
            if not template.products:
                continue

            if template.magento_product_type == 'configurable':
                # template -> configurable
                if template.attachments:
                    code = template.base_code
                    if code:
                        images = self.magento_images_from_attachments(template.attachments)
                        if images:
                            self.create_update_magento_images(app, self, code, images)
                # variants -> simple
                for product in template.products:
                    if not product.attachments:
                        continue
                    if not product.code:
                        continue
                    code = product.code
                    images = self.magento_images_from_attachments(product.attachments)
                    if images:
                        self.create_update_magento_images(app, self, code, images)
            elif template.attachments:
                if not template.attachments:
                    continue
                product, = template.products
                if not product.code:
                    continue
                code = product.code
                images = self.magento_images_from_attachments(template.attachments)
                if images:
                    self.create_update_magento_images(app, self, code, images)
            else:
                continue

        logger.info(
            'Magento %s. End export images %s products.' % (
                self.name, len(templates)))

    @staticmethod
    def magento_images_from_attachments(attachments):
        images = []
        for attachment in attachments:
            if attachment.esale_available:
                # Check if attachment is a image file
                image_mime = guess_type(attachment.name)
                if not image_mime:
                    message = 'Magento. Error export image %s ' \
                        'have not mime' % (attachment.name)
                    logger.error(message)
                    continue
                mime = image_mime[0]
                if not mime in _MIME_TYPES:
                    message = 'Magento. Error export image %s ' \
                        'is not mime valid' % (attachment.name)
                    logger.error(message)
                    continue

                # Get types image
                types = []
                if attachment.esale_base_image:
                    types.append('image')
                if attachment.esale_small_image:
                    types.append('small_image')
                if attachment.esale_thumbnail:
                    types.append('thumbnail')

                # Create dict values
                data = {}
                data['label'] = attachment.description
                data['position'] = attachment.esale_position
                data['exclude'] = attachment.esale_exclude
                data['types'] = types
                data['data'] = attachment.data
                data['name'] = attachment.name.split('.')[0] #remove ext file
                data['file'] = '/%s/%s/%s' % (
                        attachment.name[0],
                        attachment.name[1],
                        attachment.name,
                        ) # m/y/my_image.jpg
                data['mime'] = mime
                data['attachment'] = attachment
                images.append(data)
        return images

    @staticmethod
    def create_update_magento_images(app, shop, code, images):
        '''Create/Update image by code product'''
        pool = Pool()
        Attachment = pool.get('ir.attachment')

        with ProductImages(app.uri, app.username, app.password) as product_image_api:
            # find images available every product
            creates = []
            updates = []

            mgn_imgs = product_image_api.list(code, identifierType=app.identifier_type)
            for image in images:
                if image.get('file') in [mgn_img.get('file') for mgn_img in mgn_imgs]:
                    updates.append(image)
                else:
                    creates.append(image)

            # Update images
            for data in updates:
                filename = data['file']
                img_data = {}
                img_data['label'] = data['label']
                img_data['position'] = data['position']
                img_data['exclude'] = data['exclude']
                img_data['types'] = data['types']

                try:
                    product_image_api.update(code, filename, img_data)
                    message = 'Magento %s. Updated image %s product %s.' % (
                            shop.name, filename, code)
                    logger.info(message)
                except Exception, e:
                    message = 'Magento %s. Error update image %s to product %s: %s' % (
                                shop.name, filename, code, e)
                    logger.error(message)

            # Create images
            for data in creates:
                filedata = data.get('data')
                if not filedata:
                    continue

                name = data['name']
                filename = data['file']
                mime = data['mime']
                attachment = data['attachment']
                img_data = {}
                img_data['label'] = data['label']
                img_data['position'] = data['position']
                img_data['exclude'] = data['exclude']
                img_data['types'] = data['types']

                fdata = {'file': {
                    'content': base64.b64encode(filedata),
                    'name': name,
                    'mime': mime,
                    }}
                try:
                    mgn_img = product_image_api.create(code, fdata, identifierType=app.identifier_type)
                    product_image_api.update(code, mgn_img, img_data, identifierType=app.identifier_type)
                    new_name = mgn_img.split('/')[-1]
                    Attachment.write([attachment], {'name': new_name})
                    message = 'Magento %s. Created image %s product %s.' % (
                            shop.name, new_name, code)
                    logger.info(message)
                except Exception, e:
                    message = 'Magento %s. Error create image %s to product %s: %s' % (
                                shop.name, filename, code, e)
                    logger.error(message)

    def export_menus_magento(self, tpls=[]):
        """Export Menus to Magento
        :param shop: object
        :param tpls: list
        """
        self.raise_user_error('export_menus')

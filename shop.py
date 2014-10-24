#This file is part magento_product module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

import datetime
import logging
import threading
from mimetypes import guess_type
import base64

from magento import *

__all__ = ['SaleShop']
__metaclass__ = PoolMeta
_MIME_TYPES = ['image/jpeg', 'image/png']

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
                price = Product.get_sale_price([product], quantity)[product.id]
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
                    special_price = Product.get_sale_price([product], quantity)[product.id]
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
                    gprice = Product.get_sale_price([product], quantity)[product.id]

                if gprice > 0.0:
                    if self.esale_tax_include:
                        gprice = self.esale_price_w_taxes(product, gprice, quantity)
                    group_price.append({
                        'cust_group': group_prices.group.customer_group,
                        'price': str(gprice),
                        })

        data = {}
        data['price'] = str(price)
        data['special_price'] = str(special_price)
        if shop_special_price:
            special_price_from = product.template.special_price_from
            special_price_to = product.template.special_price_to
            data['special_from_date'] = str(special_price_from) if special_price_from else ''
            data['special_to_date'] = str(special_price_to) if special_price_to else ''
        data['group_price'] = group_price
        return data

    def magento_product_domain(self):
        '''Domain filter Products'''
        return [
                ('esale_available', '=', True),
                ('esale_saleshops', 'in', [self.id]),
                ]

    def export_products_magento(self, tpls=[]):
        """Export Products to Magento
        :param tpls: list
        """
        pool = Pool()
        Template = pool.get('product.template')

        product_domain = self.magento_product_domain()

        if tpls:
            templates = []
            product_domain += [('id', 'in', tpls)]
            for t in Template.search(product_domain):
                templates.append(t)
        else:
            now = datetime.datetime.now()
            last_products = self.esale_last_products

            product_domain += [['OR',
                        ('create_date', '>=', last_products),
                        ('write_date', '>', last_products),
                    ]]
            templates = Template.search(product_domain)

            # Update date last import
            self.write([self], {'esale_last_products': now})

        if not templates:
            logging.getLogger('magento').info(
                'Magento %s. Not products to export.' % (self.name))
        else:
            logging.getLogger('magento').info(
                'Magento %s. Start export %s product(s).' % (
                    self.name, len(templates)))

            user = self.get_shop_user()

            db_name = Transaction().cursor.dbname
            thread1 = threading.Thread(target=self.export_products_magento_thread, 
                args=(db_name, user.id, self.id, templates,))
            thread1.start()

    def export_products_magento_thread(self, db_name, user, sale_shop, templates):
        """Export products to Magento APP
        :param db_name: str
        :param user: int
        :param sale_shop: int
        :param templates: list
        """

        with Transaction().start(db_name, user):
            pool = Pool()
            SaleShop = pool.get('sale.shop')
            ProductTemplate = pool.get('product.template')
            ProductProduct = pool.get('product.product')
            MagentoExternalReferential = pool.get('magento.external.referential')
            BaseExternalMapping = pool.get('base.external.mapping')

            shop, = SaleShop.browse([sale_shop])
            app = shop.magento_website.magento_app

            if not app.template_mapping or not app.product_mapping:
                message = 'Add Mapping Product in Magento APP.'
                logging.getLogger('magento').error(message)
                return
            template_mapping = app.template_mapping.name
            product_mapping = app.product_mapping.name

            with Product(app.uri, app.username, app.password) as product_api:
                for template in ProductTemplate.browse(templates):
                    if not template.esale_attribute_group:
                        message = 'Magento %s. Error export template ID %s. ' \
                                'Select eSale Attribute' % (shop.name, template.id)
                        logging.getLogger('magento').error(message)
                        continue

                    for product in template.products:
                        code = product.code
                        if not code:
                            message = 'Magento %s. Error export product ID %s. ' \
                                    'Add a code' % (shop.name, product.id)
                            logging.getLogger('magento').error(message)
                            continue

                        tvals, = BaseExternalMapping.map_tryton_to_external(template_mapping, [template.id])
                        pvals, = BaseExternalMapping.map_tryton_to_external(product_mapping, [product.id])
                        prices = shop.magento_get_prices(product)

                        values = {}
                        values.update(pvals)
                        values.update(tvals)
                        values.update(prices)

                        values['categories'] = [menu.magento_id for menu in product.template.esale_menus if menu.magento_app == app]

                        websites = []
                        for shop in product.template.esale_saleshops:
                            ext_ref = MagentoExternalReferential.get_try2mgn(app,
                                    'magento.website',
                                    shop.magento_website.id)
                            if ext_ref:
                                websites.append(ext_ref.mgn_id)
                        values['websites'] = websites

                        status = values.get('status', True)
                        if not status:
                            values['status'] = '2' # 2 is dissable

                        if not values.get('tax_class_id'):
                            for tax in app.magento_taxes:
                                values['tax_class_id'] = tax.tax_id
                                break

                        del values['id']

                        if app.debug:
                            message = 'Magento %s. Product: %s. Values: %s' % (
                                    shop.name, code, values)
                            logging.getLogger('magento').info(message)

                        mgn_prods = product_api.list({'sku': {'=': code}})

                        try:
                            if mgn_prods:
                                action = 'update'
                                product_api.update(code, values)
                            else:
                                action = 'create'
                                del values['sku']

                                magento_product_type = product.template.magento_product_type

                                ext_ref = MagentoExternalReferential.get_try2mgn(app,
                                        'esale.attribute.group',
                                        product.esale_attribute_group.id)
                                attribute_mgn = ext_ref.mgn_id

                                mgn_id = product_api.create(magento_product_type, attribute_mgn, code, values)

                                message = 'Magento %s. %s product %s. Magento ID %s' % (
                                        shop.name, action.capitalize(), code, mgn_id)
                                logging.getLogger('magento').info(message)
                        except Exception, e:
                            action = None
                            message = 'Magento %s. Error export product %s: %s' % (
                                        shop.name, code, e)
                            logging.getLogger('magento').error(message)

                        if not action:
                            continue

                        # save products by language
                        for lang in app.languages:
                            with Transaction().set_context(language=lang.lang.code):
                                product = ProductProduct(product.id)
                                tvals, = BaseExternalMapping.map_tryton_to_external(template_mapping, [product.template.id])
                                pvals, = BaseExternalMapping.map_tryton_to_external(product_mapping, [product.id])
                            values = dict(pvals, **tvals)

                            if app.debug:
                                message = 'Magento %s. Product: %s. Values: %s' % (
                                        shop.name, code, values)
                                logging.getLogger('magento').info(message)

                            product_api.update(code, values, lang.storeview.code)

                            message = 'Magento %s. Update product %s (%s)' % (
                                    shop.name, code, lang.lang.code)
                            logging.getLogger('magento').info(message)

                    self.export_stocks_magento([template]) # Export Inventory - Stock
                    self.export_images_magento(shop, [template]) # Export Images
                    #TODO: Export Product Links

            Transaction().cursor.commit()
            logging.getLogger('magento').info(
                'Magento %s. End export prices %s products.' % (
                    shop.name, len(templates)))

    def export_prices_magento(self, shop, tpls=[]):
        """Export Prices to Magento
        :param shop: object
        :param tpls: list
        """
        pool = Pool()
        Template = pool.get('product.template')

        if tpls:
            templates = []
            for t in Template.browse(tpls):
                shops = [s.id for s in t.esale_saleshops]
                if t.esale_available and shop.id in shops:
                    templates.append(t)
        else:
            now = datetime.datetime.now()
            last_prices = shop.esale_last_prices

            templates = Template.search([
                    ('esale_available', '=', True),
                    ('esale_saleshops', 'in', [shop.id]),
                    ['OR',
                        ('create_date', '>=', last_prices),
                        ('write_date', '>', last_prices),
                    ]])

            # Update date last import
            self.write([shop], {'esale_last_prices': now})

        if not templates:
            logging.getLogger('magento').info(
                'Magento %s. Not products to export prices.' % (shop.name))
        else:
            logging.getLogger('magento').info(
                'Magento %s. Start export prices. %s product(s).' % (
                    shop.name, len(templates)))

            user = self.get_shop_user()

            db_name = Transaction().cursor.dbname
            thread1 = threading.Thread(target=self.export_prices_magento_thread, 
                args=(db_name, user.id, shop.id, templates,))
            thread1.start()

    def export_prices_magento_thread(self, db_name, user, sale_shop, templates):
        """Export product price to Magento APP
        :param db_name: str
        :param user: int
        :param sale_shop: int
        :param templates: list
        """

        with Transaction().start(db_name, user):
            pool = Pool()
            SaleShop = pool.get('sale.shop')
            Template = pool.get('product.template')
            MagentoExternalReferential = pool.get('magento.external.referential')

            shop, = SaleShop.browse([sale_shop])
            app = shop.magento_website.magento_app

            with Product(app.uri, app.username, app.password) as product_api:
                for template in Template.browse(templates):
                    for product in template.products:
                        code = product.code
                        if not code:
                            continue

                        data = self.magento_get_prices(shop, product)

                        if app.debug:
                            message = 'Magento %s. Product: %s. Data: %s' % (
                                    shop.name, code, data)
                            logging.getLogger('magento').info(message)

                        try:
                            if app.catalog_price == 'website':
                                ext_ref = MagentoExternalReferential.get_try2mgn(app,
                                        'magento.external.referential',
                                        shop.magento_website.id)
                                magento_website = ext_ref.mgn_id
                                product_api.update(code, data, magento_website)
                                if shop.magento_price_global: # Global price
                                    product_api.update(code, data) 
                            else:
                                product_api.update(code, data)

                            message = 'Magento %s. Export price %s product.' % (
                                    shop.name, code)
                            logging.getLogger('magento').info(message)
                        except Exception, e:
                            message = 'Magento %s. Error export prices to product %s: %s' % (
                                        shop.name, code, e)
                            logging.getLogger('magento').error(message)

            Transaction().cursor.commit()
            logging.getLogger('magento').info(
                'Magento %s. End export prices %s products.' % (
                    shop.name, len(templates)))

    def export_images_magento(self, shop, tpls=[]):
        """Export Images to Magento
        :param shop: object
        :param tpls: list
        """
        pool = Pool()
        Template = pool.get('product.template')

        if tpls:
            templates = []
            for t in Template.browse(tpls):
                shops = [s.id for s in t.esale_saleshops]
                if t.esale_available and shop.id in shops:
                    templates.append(t)
        else:
            now = datetime.datetime.now()
            last_images = shop.esale_last_images

            templates = Template.search([
                    ('esale_available', '=', True),
                    ('esale_saleshops', 'in', [shop.id]),
                    ['OR',
                        ('create_date', '>=', last_images),
                        ('write_date', '>', last_images),
                    ]])

            # Update date last import
            self.write([shop], {'esale_last_images': now})

        if not templates:
            logging.getLogger('magento').info(
                'Magento %s. Not product images to export.' % (shop.name))
        else:
            logging.getLogger('magento').info(
                'Magento %s. Start export images. %s product(s).' % (
                    shop.name, len(templates)))

            user = self.get_shop_user()

            db_name = Transaction().cursor.dbname
            thread1 = threading.Thread(target=self.export_images_magento_thread, 
                args=(db_name, user.id, shop.id, templates,))
            thread1.start()

    def export_images_magento_thread(self, db_name, user, sale_shop, templates):
        """Export product images to Magento APP
        :param db_name: str
        :param user: int
        :param sale_shop: int
        :param templates: list
        """

        with Transaction().start(db_name, user):
            pool = Pool()
            SaleShop = pool.get('sale.shop')
            Template = pool.get('product.template')
            Attachment = pool.get('ir.attachment')

            shop, = SaleShop.browse([sale_shop])
            app = shop.magento_website.magento_app

            with ProductImages(app.uri, app.username, app.password) as product_image_api:
                for template in Template.browse(templates):
                    if not template.attachments:
                        continue

                    images = []
                    for attachment in template.attachments:
                        if attachment.esale_available:
                            # Check if attachment is a image file
                            image_mime = guess_type(attachment.name)
                            if not image_mime:
                                message = 'Magento %s. Error export image %s ' \
                                    'have not mime' % (
                                        shop.name, attachment.name)
                                logging.getLogger('magento').error(message)
                                continue
                            mime = image_mime[0]
                            if not mime in _MIME_TYPES:
                                message = 'Magento %s. Error export image %s ' \
                                    'is not mime valid' % (
                                        shop.name, attachment.name)
                                logging.getLogger('magento').error(message)
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

                    for product in template.products:
                        code = product.code
                        if not code:
                            continue

                        # find images available every product
                        creates = []
                        updates = []
                        mgn_imgs = product_image_api.list(code)
                        for image in images:
                            if image.get('file') in [mgn_img.get('file') for mgn_img in mgn_imgs]:
                                updates.append(image)
                            else:
                                creates.append(image)

                        # Update images
                        for data in updates:
                            filename = data['file']
                            del data['data']
                            del data['name']
                            del data['file']
                            del data['mime']
                            del data['attachment']

                            try:
                                product_image_api.update(code, filename, data)
                                message = 'Magento %s. Updated image %s product %s.' % (
                                        shop.name, filename, code)
                                logging.getLogger('magento').info(message)
                            except Exception, e:
                                message = 'Magento %s. Error update image %s to product %s: %s' % (
                                            shop.name, filename, code, e)
                                logging.getLogger('magento').error(message)

                        # Create images
                        for data in creates:
                            filedata = data.get('data')
                            name = data['name']
                            filename = data['file']
                            mime = data['mime']
                            attachment = data['attachment']
                            del data['data']
                            del data['file']
                            del data['name']
                            del data['mime']
                            del data['attachment']

                            fdata = {'file': {
                                'content': base64.b64encode(filedata),
                                'name': name,
                                'mime': mime,
                                }}
                            try:
                                mgn_img = product_image_api.create(code, fdata)
                                product_image_api.update(code, mgn_img, data)
                                new_name = mgn_img.split('/')[-1]
                                Attachment.write([attachment], {'name': new_name})
                                message = 'Magento %s. Created image %s product %s.' % (
                                        shop.name, new_name, code)
                                logging.getLogger('magento').info(message)
                            except Exception, e:
                                message = 'Magento %s. Error create image %s to product %s: %s' % (
                                            shop.name, filename, code, e)
                                logging.getLogger('magento').error(message)

            Transaction().cursor.commit()
            logging.getLogger('magento').info(
                'Magento %s. End export images %s products.' % (
                    shop.name, len(templates)))

    def export_stocks_magento(self, tpls=[]):
        """Export Stock to Magento. Install magento stock module
        :param shop: object
        :param tpls: list
        """
        pass

    def export_menus_magento(self, shop, tpls=[]):
        """Export Menus to Magento
        :param shop: object
        :param tpls: list
        """
        self.raise_user_error('export_menus')

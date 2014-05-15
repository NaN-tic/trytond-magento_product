#This file is part magento_product module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

from decimal import Decimal
import datetime
import logging
import threading

from magento import *

__all__ = ['SaleShop']
__metaclass__ = PoolMeta


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
    def magento_get_prices(self, shop, product, quantity=1):
        """
        Get Products Price, Sepcial Price and Group price
        from price list or price (with or not taxes)
        :param shop: object
        :param product: object
        :param quantity: int
        :return dicc
        """
        pool = Pool()
        Product = pool.get('product.product')

        # Sale Price
        price = 0
        if shop.esale_price == 'pricelist' and shop.price_list:
            context = {
                'price_list': shop.price_list.id,
                'customer': shop.esale_price_party.id,
                'without_special_price': True,
                }
            with Transaction().set_context(context):
                price = Product.get_sale_price([product], quantity)[product.id]
        else:
            price = product.template.list_price

        if shop.esale_tax_include:
            price = self.esale_price_w_taxes(product, price, quantity)

        # Special Price
        special_price = ''
        if shop.special_price:
            if shop.type_special_price == 'pricelist':
                context = {
                    'price_list': shop.price_list.id,
                    'customer': shop.esale_price_party.id,
                    }
                with Transaction().set_context(context):
                    special_price = Product.get_sale_price([product], quantity)[product.id]
            else:
                special_price = product.template.special_price or 0

            if shop.esale_tax_include:
                special_price = self.esale_price_w_taxes(product, special_price, quantity)

            if not (special_price > 0.0 and special_price < price):
                special_price = ''

        # Group Price
        group_price = []
        if shop.magento_shop_group_prices and product.magento_group_price:
            # {'cust_group': '0', 'website_price': '10.0000', 'price': '10.0000', 
            # 'website_id': '0', 'price_id': '1', 'all_groups': '0'}
            for group_prices in shop.magento_shop_group_prices:
                context = {
                    'price_list': group_prices.price_list.id,
                    'customer': shop.esale_price_party.id,
                    }
                with Transaction().set_context(context):
                    price = Product.get_sale_price([product], quantity)[product.id]

                if price > 0.0:
                    if shop.esale_tax_include:
                        price = self.esale_price_w_taxes(product, price, quantity)
                    group_price.append({
                        'cust_group': group_prices.group.customer_group,
                        'price': str(price),
                        })
        return {
            'price':price,
            'special_price':special_price,
            'group_price': group_price,
            }

    def export_products_magento(self, shop, tpls=[]):
        """Export Products to Magento
        :param shop: object
        :param tpls: list
        """
        #TODO: Export Tryton product
        active_ids = Transaction().context.get('active_ids')

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
                'Magento %s. Start export prices %s products.' % (
                    shop.name, len(templates)))

            user = self.get_shop_user(shop)

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
                        special_price_from = product.template.special_price_from
                        special_price_to = product.template.special_price_to

                        data = {}
                        prices = self.magento_get_prices(shop, product)
                        data['price'] = str(prices['price'])
                        data['special_price'] = str(prices['special_price'])
                        data['special_from_date'] = str(special_price_from) if special_price_from else ''
                        data['special_to_date'] = str(special_price_to) if special_price_to else ''
                        data['group_price'] = prices['group_price']

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
                        except:
                            message = 'Magento %s. Error export prices to product %s.' % (
                                        shop.name, code)
                            logging.getLogger('magento').error(message)

            Transaction().cursor.commit()
            logging.getLogger('magento').info(
                'Magento %s. End export prices %s products.' % (
                    shop.name, len(templates)))

    def export_stocks_magento(self, shop, tpls=[]):
        """Export Stocks to Magento
        :param shop: object
        :param tpls: list
        """
        #TODO: Export Tryton stocks
        active_ids = Transaction().context.get('active_ids')

    def export_images_magento(self, shop, tpls=[]):
        """Export Images to Magento
        :param shop: object
        :param tpls: list
        """
        #TODO: Export Tryton images
        active_ids = Transaction().context.get('active_ids')

    def export_menus_magento(self, shop, tpls=[]):
        """Export Menus to Magento
        :param shop: object
        :param tpls: list
        """
        self.raise_user_error('export_menus')

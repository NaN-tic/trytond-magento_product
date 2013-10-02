#This file is part magento_product module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.transaction import Transaction
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['SaleShop']
__metaclass__ = PoolMeta

class SaleShop:
    __name__ = 'sale.shop'

    def export_status_magento(self, shop):
        """Export Status Orders to Magento
        :param shop: Obj
        """
        #TODO: Export Magento Orders
        return True

    def export_products_magento(self, shop):
        """Export Products to Magento
        :param shop: Obj
        """
        #TODO: Export Tryton product
        active_ids = Transaction().context.get('active_ids')
        return True

    def export_prices_magento(self, shop):
        """Export Prices to Magento
        :param shop: Obj
        """
        #TODO: Export Tryton prices
        active_ids = Transaction().context.get('active_ids')
        return True

    def export_stocks_magento(self, shop):
        """Export Stocks to Magento
        :param shop: Obj
        """
        #TODO: Export Tryton stocks
        active_ids = Transaction().context.get('active_ids')
        return True

    def export_images_magento(self, shop):
        """Export Images to Magento
        :param shop: Obj
        """
        #TODO: Export Tryton images
        active_ids = Transaction().context.get('active_ids')
        return True

    def export_menus_magento(self, shop):
        """Export Menus to Magento
        :param shop: Obj
        """
        #TODO: Export Tryton menus
        return True

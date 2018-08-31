# This file is part magento_product module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import product
from . import magento_core
from . import menu
from . import shop

def register():
    Pool.register(
        magento_core.MagentoApp,
        magento_core.MagentoSaleShopGroupPrice,
        product.MagentoProductType,
        product.MagentoAttributeConfigurable,
        menu.CatalogMenu,
        product.Template,
        product.TemplateMagentoAttributeConfigurable,
        product.Product,
        shop.SaleShop,
        module='magento_product', type_='model')

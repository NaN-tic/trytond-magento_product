#This file is part magento_product module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.pool import Pool
from .product import *
from .magento_core import *
from .shop import *

def register():
    Pool.register(
        MagentoApp,
        MagentoProductType,
        Product,
        SaleShop,
        module='magento_product', type_='model')

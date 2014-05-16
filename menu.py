#This file is part magento_product module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta

__all__ = ['CatalogMenu']
__metaclass__ = PoolMeta


class CatalogMenu:
    __name__ = 'esale.catalog.menu'
    magento_app = fields.Many2One('magento.app', 'Magento APP')
    magento_id = fields.Integer('External ID')

    @classmethod
    def copy(cls, menus, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['magento_app'] = None
        default['magento_id'] = None
        return super(CatalogMenu, cls).copy(menus, default=default)

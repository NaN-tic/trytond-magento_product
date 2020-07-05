# This file is part magento_product module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields, Unique
from trytond.pool import PoolMeta
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['CatalogMenu']


class CatalogMenu(metaclass=PoolMeta):
    __name__ = 'esale.catalog.menu'
    magento_app = fields.Many2One('magento.app', 'Magento APP')
    magento_id = fields.Integer('External ID')

    @classmethod
    def __setup__(cls):
        super(CatalogMenu, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('categ_uniq', Unique(t, t.magento_app, t.magento_id),
                'Category of product must be unique for every eShop.'),
        ]

    @classmethod
    def copy(cls, menus, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['magento_app'] = None
        default['magento_id'] = None
        return super(CatalogMenu, cls).copy(menus, default=default)

    @classmethod
    def delete(cls, menus):
        for menu in menus:
            if menu.magento_id:
                raise UserError(gettext('magento_product.msg_delete_esale_menu'),
                    menu=menu.rec_name,
                    magento=menu.magento_app.name)
        super(CatalogMenu, cls).delete(menus)

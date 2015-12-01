# This file is part of the magento_product module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class MagentoProductTestCase(ModuleTestCase):
    'Test Magento Product module'
    module = 'magento_product'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        MagentoProductTestCase))
    return suite
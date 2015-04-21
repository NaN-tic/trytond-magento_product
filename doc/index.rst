Magento Product Module
######################

The magento_product module add sync/import Products from/to Magento APP.

Import Categories
-----------------

In Magento APP, add Magento ID Root Category and create tree menus.

If and category exist (search by Magento APP and ID Category), update category.

Import Products
---------------

After import categories you could import products. If you not import new categories
before import products, these categories there aren't available in menus and products.

Add in Magento APP Base External Mapping:

* Product Template
* Product Product

Not necessary to create a Base External Mapping fields:

* shops
* customer_taxes
* list_price
* cost_price
* esale_menus

In Magento APP, add rang of Product IDs or rang date from/to
(find Magento products where create+update contain this rang).

If find a product by code, is updated.

Import Cross Sell, Up Sell, Related
-----------------------------------

After import products to Tryton, you could import cross sell, up sell and
related products and update products in ERP. If you not import new products
before import products links, these links there aren't available products.

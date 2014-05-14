=================
Productos Magento
=================

El módulo Productos Magento sincroniza el catálogo de productos de Magento con
el catálogo de productos de Tryton.

Importar Categorias
-------------------

En Magento APP, añadimos el ID Root Category para crear el árbol de menús (categorias).

Si una categoría existe (se busca por Magento APP y ID categoría) se actualizará.

Importar Productos
------------------

Una vez importadas las categorias podrá importar los productos. En el caso que un producto
de Magento contenga una categoría que no haya importado antes (nueva), el producto no
constará esta categoría.

Añade en Magento APP los Base External Mapping:

* Product Template
* Product Product

No es necesario crear en el Base External Mapping los campos:

* esale_saleshops
* customer_taxes
* list_price
* cost_price
* esale_menus

En Magento APP, añade un rango de IDs de productos o un rango de fecha 
desde/to para importar los productos (se busca a Magento todos los productos
que se hayan creado/actualizado por este rango de fechas).

Si el producto por código existe, este será actualizado.

En la importación de productos también se importan las traducciones (store views) y las
imagenes que esten publicados a Magento (se nos guarda en el disco duro del servidor de Tryton).

Importar Ventas cruzadas, Ventas sugeridas y Productos relacionados
-------------------------------------------------------------------

Después de importar los productos, podrá importa las ventas cruzadas,
ventas sugeridas y relacionados para actualizar los productos en el ERP.

Es importate como en el caso de las categorias, disponer todos los productos importados
a Tryton antes de importar nuevos datos.

En Magento APP, añade un rango de IDs de productos para importar las ventas cruzadas,
ventas sugeridas y relacionados con los productos que seleccione en el rango.

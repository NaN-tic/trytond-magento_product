#:before:magento/magento:section:pedidos#

.. inheritref:: magento/magento:section:productos

Productos
=========

.. inheritref:: magento/magento:section:importacion_de_productos

Importación productos
=====================

Para importar productos de Magento a Tryton abra el menú |menu_magento_app| y
en la pestaña **Importar** verá los botones de importación de Magento a Tryton
siguientes:

.. |menu_magento_app| tryref:: magento.menu_magento_app_form/complete_name

* Importar tipos de productos (simple, configurable, ...). Posteriormente, a 
  través del menú |menu_magento_product_type|\ , podrá activar con que
  productos trabaja. Este campo es requerido.
* Importar grupo de productos (default,...) que haya definido en Magento. Este
  campo es requerido.
* Importar Magento Categorías. Importa el árbol de navegación de Magento. Si la categoría
  ya existe al ERP, esta se actualizará con los datos de Magento. En el caso que desea
  eliminar una categoría, a parte de que no se recomienda por no obtener el mensaje de
  "Error 404 Not Found", puede marcar la opción "Activo" a "No" para que no esté disponible.
* Importar/Actualizar Productos Magento. Importa o actualiza los productos que disponga en el ERP
  con los productos que importe del catálogo de Magento. En catálogos de muchos productos,
  esta importación se debe realizar por intervalos de fechas o por rango de IDs. Puede hacerlo
  cada 500 o 1000 productos. Revise los logs del sistema.
  Antes de importar nuevos productos, debe importar las nuevas categorías que haya creado desde
  la última importación. En el caso que una categoría no se encuentre a Tryton no se dispondrá
  en el producto.
  En la importación de productos también importará las traducciones y las imagenes.
  Para las traducciones debe especificar en Magento APP los idiomas que corresponden a la vista
  de la tienda de Magento.
  Para las imagenes, antes de crear una nueva imagen, se buscar si en la plantilla de producto
  ya dispone de un imagen por el nombre de la imagen. La imagen que se importa se dispone como adjunto
  en el producto (se guarda al disco duro del servidor Tryton).
  Si el producto ya exite en Tryton, este se actualizará excepto los campos "Precio venta", "Precio de coste"
  y "Impuestos de cliente" (los precios e impuestos del ERP tienen preferencia respeto a Magento).
* Importar links de productos. Actualiza los productos importados con los productos
  Ventas cruzadas, Ventas sugeridas y Productos relacionados. Antes de importar nuevos links de productos,
  debe importar los nuevos productos que haya creado desde la última importación. En el caso que 
  una producto no se encuentre a Tryton no se dispondrá como link en el producto.

.. |menu_magento_product_type| tryref:: magento_product.menu_magento_product_type_form/complete_name

.. figure:: images/tryton-magento-importar-productos.png

.. inheritref:: magento/magento:section:importacion_de_atributos

Importación de atributos
========================

En Magento APP dispone de la importación de atributos:

* Importar grupo de atributos: Importa el grupo de atributo.
* Importar opciones de atributos: Importa las opciones en los campos selección
  de los atributos de producto de Magento a Tryton.

No se dispone de ninguna importación de atributos para evitar crear atributos que no
sean necesarios al ERP. Después de importar los grupos de atributos, deberá crear
los atributos que desea gestionar a Productos/Atributos. En el caso de los atributos
del tipo "selección" puede importar las opciones mediante el botón "Importar opciones de atributos".

Recuerde que si estos atributos desean después importar/exportar entre Tryton <-> Magento deberá
crear el tipo de mapeo que se va realizar entre los campos del ERP y los campos de Magento.

.. inheritref:: magento/magento:section:exportacion_de_categorias_de_productos

Exportación de categorías de productos
======================================

A diferencia de las otras exportaciones (productos, precios, ...) la exportación
de categorías no se realiza en la tienda, si no desde el Magento App.

En la pestaña "Exportar" de Magento APP dispone del botón "Exportar categorías a Magento"
donde podrá exportar todo el árbol de categorías de Magento.

Deberá seleccionar la categoría root (principal) de Magento. En este momento se
crearán/actualizarán los menús definidos al ERP como categorías a Magento.

Es importante si crea nuevas categorías, antes de exportar productos, primero se exporte
las categorías para que estén disponibles a Magento antes de exportar productos.

Para eliminar una categoría a Magento, debe desmarcar la opción "Activo". La categoría publicada a Magento
nunca se elimina; simplemente se muestrará o quedará oculto y también deberá evitar una vez publicado una
categoría obtener el error "404 NOT Found" de los buscadores.

En la descripción de la categoría puede usar HTML para formatear el texto. Recomendamos el uso de la sintaxis
wiki para el formateo de texto. Usando la sintaxis de wiki le permite controlar el texto HTML resultante como
más fácil para la lectura. `Ejemplos de la sintaxis wiki: <http://meta.wikimedia.org/wiki/Help:Wikitext_examples>`_ 
En los campos de SEO no se debe usar el formato HTML.

.. inheritref:: magento/magento:section:exportacion_de_productos

Exportación de productos
========================

A la tienda dispone de las opciones para la exportación de productos a Magento. Mediante
el botón "Exportar productos" exportará todos los productos a partir de la fecha de creación
o modificación de un producto (plantilla de producto). Esta acción obtendrá todos los productos
con la condición:

* Disponible en eSale
* El producto esté disponible en la tienda
* La fecha de creación/modificación sea mayor que la que especificamos

También en los productos dispone de un asistente para seleccionar productos y exportar
sólo estos productos a la tienda que seleccione en el asistente (pasarán a posterior
una verificación que estén disponibles al eSale y a la tienda que hemos seleccionado).

La información que se enviará a Magento proviene de los Mappings que haya definido en Magento App.
(Administración/Modelos/Base External Mapping). En estos campos, se añadiran los siguientes campos:

* Categorías: Los menús que disponga el producto (y pertenezca al Magento App). Si ha creado una categoría
  nueva al ERP, antes de sincronizar productos recuerde de exportar primero las categorias.
* Websites: Las tiendas que disponga el producto (y pertenezca al Magento App).
* Impuesto: Si no ha definido ningún atributo del impuesto, usará el primer impuesto definido
  en Magento APP, en el apartado de Impuestos.

Los campos que no debe olbidar para los productos de Magento son:

* Tipo de producto (por defecto simple)
* Atributo
* Código de producto

Recuerde de asignar valores por defecto para estos campos.

La exportación de productos también exportará:

* Las traducciones del producto (según los idiomas definidos en Magento App)
* Inventario o stock del producto (cantidad y gestión del stock)
* Imágenes (si dispone de la opción "Disponible eSale")

Para eliminar un producto a Magento, debe desmarcar la opción "Activo" del eSale. El producto nunca se elimina; simplemente
se muestrará o quedará oculto y también deberá evitar una vez publicado un producto obtener el error "404 NOT Found"
de los buscadores.

En la descripción y la descripción corta del producto puede usar HTML para formatear el texto. Recomendamos el uso de la sintaxis
wiki para el formateo de texto. Usando la sintaxis de wiki le permite controlar el texto HTML resultante como
más fácil para la lectura. `Ejemplos de la sintaxis wiki: <http://meta.wikimedia.org/wiki/Help:Wikitext_examples>`_ 
En los campos de SEO no se debe usar el formato HTML.

.. inheritref:: magento/magento:section:exportacion_de_productos_configurables

Exportación productos configurables
-----------------------------------

En el caso que Magento use productos del tipo "Configurable", deberemos marcar en la plantilla
eSale la opción del tipo de producto configurable. Al activar esta opción deberemos añadir los atributos
configurables relacionados con el producto (campo requerido). También el campo "Código base" del producto
pasará a ser un campo requerido.

Es importante antes de exportar el producto a Magento, seleccionar los atributos configurables
relacionados con el producto que usará. Después de la exportación, no podrá se actualizará el producto
a Magento con nuevos productos. En el caso que desea actualizar los atributos configurables que usará
el producto, deberá eliminar el producto a Magento y volver a exportar.

Para que las variantes del producto queden relacionados con los atributos configurables, también
es importante que a cada variante lo relacione con el atributo deseado.

Por ejemplo, si disponemos del atributos configurable "color", por cada variante, deberemos
seleccionar el atributo "color" y su opción. Un ejemplo gráfico seria:

* Camiseta Tryton - Roja
* Camiseta Tryton - Negra

.. inheritref:: magento/magento:section:exportacion_de_precios_de_productos

Exportación de precios de productos
===================================

A la tienda dispone de las opciones para la exportación de precios a Magento. Mediante
el botón "Exportar precios" exportará todos los precios a partir de la fecha de creación
o modificación de un producto (plantilla de producto). Esta acción obtendrá todos los productos
con la condición:

* Disponible en eSale
* El producto esté disponible en la tienda
* La fecha de creación/modificación sea mayor que la que especificamos

También en los productos dispone de un asistente para seleccionar productos y exportar
sólo estos productos a la tienda que seleccione en el asistente (pasarán a posterior
una verificación que estén disponibles al eSale y a la tienda que hemos seleccionado).

Los precios a exportar consisten en 3 bloques. Ambas opciones permiten si el precio ya incluye
los impuestos o se calcula a partir de una tarifa de precio o precio del producto.

* Precio: El precio por defecto del producto a Magento. Se calcula a partir de la tarifa de la tienda
  o el precio del producto. Si la tienda es con impuestos, el precio se le sumará los impuestos del producto.
* Precio Especial: Para activar esta opción debe activar en la tienda permite la opción de Precio Especial.
  El precio especial proviene del precio especial del producto. A este precio, se le aplicará o no la tarifa
  de precios si marca la opción en la tienda. También se sumará los impuestos si esta opción esta marcada en la tienda.
  Si el precio especial es 0 (cero) o más grande que el precio por defecto, no se exportará el precio especial.
  Si en el producto le añadimos un rango de fechas para aplicar el precio especial, estas fechas se exportaran
  en el momento de exportar el precio. 
* Grupo de precios: A la tienda, debe marcar la opción de Grupo de Precios de Magento y por cada grupo de Magento,
  seleccionar la tarifa de precios que se calculará el precio final (A la Tienda, en el apartado de Configuraciones de Magento).
  También es importante marcar la opción "Magento Grupo de Precios" en el producto, para especificar que este producto 
  permite esta opción. En el caso que la tienda sea con impuestos incluidos se le sumará la base del impuesto.
  En el caso que el precio del Grupo no sea mayor de zero, no se exportará este precio (vacío).

En Magento, los precios pueden ser Globales o por Website. En la configuración de Magento APP debe especificar
como exportar los precios (por defecto, precios globales).

.. inheritref:: magento/magento:section:exportacion_de_imagenes_de_productos

Exportación de imagenes de productos
====================================

A la tienda dispone de las opciones para la exportación de imagenes a Magento. Mediante
el botón "Exportar imagenes" exportará todos las imagenes a partir de la fecha de creación
o modificación de un producto (plantilla de producto). Esta acción obtendrá todos los productos
con la condición:

* Disponible en eSale
* El producto esté disponible en la tienda
* La fecha de creación/modificación sea mayor que la que especificamos

También en los productos dispone de un asistente para seleccionar productos y exportar
sólo estos productos a la tienda que seleccione en el asistente (pasarán a posterior
una verificación que estén disponibles al eSale y a la tienda que hemos seleccionado).

Las imagenes a exportar a Magento son adjuntos del producto:

* Disponible eSale
* El tipo de imagen sea un JPG o PNG

Si ha creado productos nuevos, antes de sincronizar imagenes debe exportar productos (al exportar
productos solamente ya publicará también las imagenes del producto).

Para eliminar una imagen de Magento, debe marcar la opción "Excluir". La imagen nunca se elimina; simplemente
se muestrará o quedará oculta.

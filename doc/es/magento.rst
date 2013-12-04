#:before:magento/magento:section:pedidos#

.. inheritref:: magento/magento:section:productos

Productos
=========

La exportación de productos de Magento a Tryton se realiza dentro de las opciones
de la tienda o por cada producto individualmente.

.. inheritref:: magento/magento:section:exportacion_de_productos

Exportación de productos
========================

Consulte la documentación del módulo
`productos de comercio electrónico <../esale_product/index.html>`_ para la
gestión de los productos y su exportación de Tryton a Magento.

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
* Importar Magento Categorías. Importa el árbol de navegación de Magento.
* Importar/Actualizar Productos Magento. Importa o actualiza los productos
  actuales a partir del catálogo de Magento. En catálogos de muchos productos,
  esta importación se debe realizar por intervalos de tiempo. Puede hacerlo
  cada 500 o 1000 productos. Revise los logs del sistema.
* Importar imágenes Magento. Importa las imágenes de Magento al ERP. Las
  imágenes serán una URL del servidor Magento (no ficheros adjuntos).

.. |menu_magento_product_type| tryref:: magento_product.menu_magento_product_type_form/complete_name

.. figure:: images/tryton-magento-importar-productos.png

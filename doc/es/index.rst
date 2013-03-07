=================
Productos Magento
=================

El módulo Productos Magento añade los botones para sincronizar el catálogo de
productos de Magento con el catálogo de productos de Tryton. Estos botones le
permiten importar y exportar los productos de Tryton a Magento y viceversa.

También añade los mapeos de los campos de los productos entre Tryton y Magento
(correspondencia de campos de los productos y cálculos) por defecto
(`Mapeo externo base <../base_external_mapping/index.html>`_)

Exportación de productos
========================

Consulte la documentación del módulo
`Productos de comercio electrónico <../esale_product/index.html>`_ para la
gestión de los productos y su exportación de Tryton a Magento.

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
* Importar Magento Categorías. Importa el árbol de navegación de Magento. Abra
  el menú |menu_menu_list|\ , para su edición.
* Importar/Actualizar Productos Magento. Importa o actualiza los productos
  actuales a partir del catálogo de Magento. En catálogos de muchos productos,
  esta importación se debe realizar por intervalos de tiempo. Puede hacerlo
  cada 500 o 1000 productos. Revise los logs del sistema.
* Importar imágenes Magento. Importa las imágenes de Magento al ERP. Las
  imágenes serán una URL del servidor Magento (no ficheros adjuntos).

.. |menu_magento_product_type| tryref:: magento_product.menu_magento_product_type_form/complete_name
.. |menu_menu_list| tryref:: esale_product.menu_menu_list/complete_name

.. figure:: images/tryton-magento-importar-productos.png

Módulos que dependen
====================

Instalados
----------

.. toctree::
   :maxdepth: 1

   /esale/index
   /esale_product/index
   /magento/index

Dependencias
------------

* `Comercio electrónico`_
* `Productos de comercio electrónico`_
* Magento_

.. _Comercio electrónico: ../esale/index.html
.. _Productos de comercio electrónico: ../esale_product/index.html
.. _Magento: ../magento/index.html

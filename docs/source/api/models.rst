Models
======

.. automodule:: objettoqt.models

   .. autoclass:: objettoqt.models.OQListModel

      .. autoattribute:: objettoqt.models.OQListModel.headersObjChanged
         :annotation:

      .. autoattribute:: objettoqt.models.OQListModel.headersActionReceived
         :annotation:

      .. autoattribute:: objettoqt.models.OQListModel.OBase
         :annotation:

      .. automethod:: objettoqt.models.OQListModel._onHeadersObjChanged
      .. automethod:: objettoqt.models.OQListModel._onHeadersActionReceived
      .. automethod:: objettoqt.models.OQListModel.headersObj
      .. automethod:: objettoqt.models.OQListModel.setHeadersObj
      .. automethod:: objettoqt.models.OQListModel.headersObjToken
      .. automethod:: objettoqt.models.OQListModel.headers
      .. automethod:: objettoqt.models.OQListModel.setHeaders
      .. automethod:: objettoqt.models.OQListModel.index
      .. automethod:: objettoqt.models.OQListModel.parent
      .. automethod:: objettoqt.models.OQListModel.headerData
      .. automethod:: objettoqt.models.OQListModel.columnCount
      .. automethod:: objettoqt.models.OQListModel.rowCount
      .. automethod:: objettoqt.models.OQListModel.flags
      .. automethod:: objettoqt.models.OQListModel.data
      .. automethod:: objettoqt.models.OQListModel.mimeType
      .. automethod:: objettoqt.models.OQListModel.mimeTypes
      .. automethod:: objettoqt.models.OQListModel.mimeData
      .. automethod:: objettoqt.models.OQListModel.supportedDropActions
      .. automethod:: objettoqt.models.OQListModel.supportedDragActions
      .. automethod:: objettoqt.models.OQListModel.dropMimeData

   .. autoclass:: objettoqt.models.AbstractListModelHeader

      .. autoattribute:: objettoqt.models.AbstractListModelHeader.title
         :annotation: :  Data Attribute

      .. autoattribute:: objettoqt.models.AbstractListModelHeader.metadata
         :annotation: :  Data Attribute

      .. automethod:: objettoqt.models.AbstractListModelHeader.flags
      .. automethod:: objettoqt.models.AbstractListModelHeader.data

   .. autoclass:: objettoqt.models.ListModelHeader

      .. autoattribute:: objettoqt.models.ListModelHeader.fallback
         :annotation: :  Data Attribute

      .. autoattribute:: objettoqt.models.ListModelHeader.default_flags
         :annotation: :  Data Attribute

      .. automethod:: objettoqt.models.ListModelHeader.flags
      .. automethod:: objettoqt.models.ListModelHeader.data

# -*- coding: utf-8 -*-
"""List model."""

from abc import abstractmethod

from objetto import POST, PRE, Application, InteractiveData, data_attribute
from objetto.bases import BaseObject
from objetto.changes import ListDelete, ListInsert, ListMove, ListUpdate
from objetto.exceptions import SerializationError
from objetto.objects import ListObject, MutableListObject, list_cls
from objetto.utils.reraise_context import ReraiseContext
from objetto.utils.type_checking import assert_is_instance
from Qt import QtCore
from six import ensure_binary, string_types
from six.moves import collections_abc
from yaml import YAMLError, safe_dump, safe_load

from .._mixins import OQAbstractItemModelMixin
from .._objects import OQObject

__all__ = [
    "OQListModel",
    "AbstractListModelHeader",
    "ListModelHeader",
]


class AbstractListModelHeader(InteractiveData):
    """
    **(abstract class)**

    To be used with :class:`objettoqt.models.OQListModel`.
    Carries information on how the value should be retrieved for a column.

    Inherits from:
      - :class:`objetto.InteractiveData`
    """

    title = data_attribute(string_types, subtypes=True, default="")
    """
    Title.

    :type: str
    """

    metadata = data_attribute(default=None)
    """
    Metadata.

    :type: str
    """

    def flags(self, obj, row):
        """
        **virtual method**

        Retrieve flags for an item at a specific row.

        :param obj: List object.
        :type obj: objetto.objects.ListObject

        :param row: Row.
        :type row: int

        :return: Flags.
        :rtype: QtCore.Qt.ItemFlag
        """
        if False and self and obj and row:  # for PyCharm
            pass
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    @abstractmethod
    def data(self, obj, row, role=QtCore.Qt.DisplayRole):
        """
        **abstract method**

        Retrieve data for an item at a specific row.

        :param obj: List object.
        :type obj: objetto.objects.ListObject

        :param row: Row.
        :type row: int

        :param role: Role.
        :type role: QtCore.Qt.ItemDataRole

        :return: Data.
        """
        raise NotImplementedError()


class ListModelHeader(AbstractListModelHeader):
    """
    To be used with :class:`objettoqt.models.OQListModel`.
    Carries information on how the value should be retrieved for a column.

    For the :attr:`QtCore.Qt.DisplayRole`, this implementation will use the
    :attr:`objettoqt.models.AbstractListModelHeader.title` as the attribute name that
    will be queried from the source object at the row.

    The fallback value will be returned if a title is provided and the object at
    the row does not have an attribute with the same name as the title.

    In the case an empty title is provided (default behavior), a string representation
    of the object at the row will be returned.

    The source object at the row can be accesed through the :attr:`QtCore.Qt.UserRole`.

    Inherits from:
      - :class:`objettoqt.models.AbstractListModelHeader`
    """

    fallback = data_attribute(string_types, subtypes=True, default="")
    """
    Fallback value.

    :type: str
    """

    default_flags = data_attribute(
        default=QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    )
    """
    Default flags.

    :type: QtCore.Qt.ItemFlag
    """

    def flags(self, obj, row):
        """
        Retrieve flags for an item at a specific row.

        :param obj: List object.
        :type obj: objetto.objects.ListObject

        :param row: Row.
        :type row: int

        :return: Flags.
        :rtype: QtCore.Qt.ItemFlag
        """
        return self.default_flags

    def data(self, obj, row, role=QtCore.Qt.DisplayRole):
        """
        Retrieve data for an item at a specific row.

        :param obj: List object.
        :type obj: objetto.objects.ListObject

        :param row: Row.
        :type row: int

        :param role: Role.
        :type role: QtCore.Qt.ItemDataRole

        :return: Data.
        :rtype: str or objetto.bases.BaseObject
        """
        with obj.app.read_context():
            if role == QtCore.Qt.DisplayRole:
                sub_obj = obj[row]
                title = self.title
                if title:
                    return str(getattr(sub_obj, title, self.fallback))
                else:
                    return str(sub_obj)
            elif role == QtCore.Qt.UserRole:
                return obj[row]


class _InternalHeaders(OQObject):
    """Internal headers object for keeping track of header changes."""

    def _onObjChanged(self, obj, old_obj, phase):
        list_model = self.parent()
        if isinstance(list_model, OQListModel):
            list_model.__onHeadersObjChanged__(obj, old_obj, phase)
            list_model._onHeadersObjChanged(obj, old_obj, phase)
            list_model.headersObjChanged.emit(obj, old_obj, phase)

    def _onActionReceived(self, action, phase):
        list_model = self.parent()
        if isinstance(list_model, OQListModel):
            list_model.__onHeadersActionReceived__(action, phase)
            list_model._onHeadersActionReceived(action, phase)
            list_model.headersActionReceived.emit(action, phase)


class OQListModel(OQAbstractItemModelMixin, QtCore.QAbstractItemModel):
    """
    Mixed :class:`QtCore.QAbstractItemModel` type (for lists).

    Observes actions sent from an instance of :class:`objetto.objects.ListObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQAbstractItemModelMixin`
      - :class:`QtCore.QAbstractItemModel`

    :param parent: Parent.
    :type parent: QtCore.QObject or None

    :param headers: Headers (or None for default).
    :type headers: tuple[objettoqt.models.AbstractListModelHeader] or None

    :param mime_type: Mime type.
    :type mime_type: str or None
    """

    headersObjChanged = QtCore.Signal(object, object, object)
    """
    **signal**

    Emitted when the headers object changes.

    :param obj: New headers list object (or None).
    :type obj: objetto.objects.ListObject or None

    :param old_obj: Old headers list object (or None).
    :type old_obj: objetto.objects.ListObject or None

    :param phase: Phase.
    :type phase: objetto.bases.Phase
    """

    headersActionReceived = QtCore.Signal(object, object)
    """
    **signal**

    Emitted when an action is received from the headers object.

    :param action: Action.
    :type action: objetto.objects.Action

    :param phase: Phase.
    :type phase: objetto.bases.Phase
    """

    OBase = ListObject
    """
    **read-only class attribute**

    Minimum `objetto` object base requirement.

    :type: type[objetto.objects.ListObject]
    """

    __default_headers_cls = list_cls(AbstractListModelHeader, subtypes=True)

    def __init__(self, parent=None, headers=None, mime_type=None, **kwargs):
        super(OQListModel, self).__init__(parent=parent, **kwargs)

        # Internal headers.
        self.__headers = _InternalHeaders(parent=self)

        # Store mime type.
        self.__mime_type = mime_type or None

        # Default headers object.
        filtered_headers = []
        for header in headers or ():
            if isinstance(header, string_types):
                header = ListModelHeader(title=header)
            else:
                with ReraiseContext(TypeError, "'header' parameter"):
                    assert_is_instance(header, AbstractListModelHeader)
            filtered_headers.append(header)
        self.__default_headers_obj = type(self).__default_headers_cls(
            Application(), filtered_headers or (ListModelHeader(),)
        )

        # Headers object (start with default).
        self.__headers.setObj(self.__default_headers_obj)

    def __onObjChanged__(self, obj, old_obj, phase):
        super(OQListModel, self).__onObjChanged__(obj, old_obj, phase)

        # Reset model.
        if phase is PRE:
            self.beginResetModel()
        elif phase is POST:
            self.endResetModel()

    def __onActionReceived__(self, action, phase):
        super(OQListModel, self).__onActionReceived__(action, phase)

        # The list changed.
        if action.sender is self.obj():

            # Insert rows.
            if isinstance(action.change, ListInsert):
                if phase is PRE:
                    self.beginInsertRows(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                elif phase is POST:
                    self.endInsertRows()

            # Delete rows.
            elif isinstance(action.change, ListDelete):
                if phase is PRE:
                    self.beginRemoveRows(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                elif phase is POST:
                    self.endRemoveRows()

            # Move rows.
            elif isinstance(action.change, ListMove):
                if phase is PRE:
                    self.beginMoveRows(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                        QtCore.QModelIndex(),
                        action.change.target_index,
                    )
                elif phase is POST:
                    self.endMoveRows()

            # Change rows.
            elif isinstance(action.change, ListUpdate):
                if phase is POST:
                    self.dataChanged.emit(
                        self.index(action.change.index, 0, QtCore.QModelIndex()),
                        self.index(
                            action.change.last_index,
                            self.columnCount() - 1,
                            QtCore.QModelIndex(),
                        ),
                    )

    def __onHeadersObjChanged__(self, obj, old_obj, phase):
        if False and obj:  # for PyCharm
            pass

        # Reset model.
        if old_obj is not None:
            if phase is PRE:
                self.beginResetModel()
            elif phase is POST:
                self.endResetModel()

    def __onHeadersActionReceived__(self, action, phase):

        # The headers changed.
        if action.sender is self.__headers.obj():

            # Insert columns.
            if isinstance(action.change, ListInsert):
                if phase is PRE:
                    self.beginInsertColumns(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                elif phase is POST:
                    self.endInsertColumns()

            # Delete columns.
            elif isinstance(action.change, ListDelete):
                if phase is PRE:
                    self.beginRemoveColumns(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                if phase is POST:
                    self.endRemoveColumns()

            # Move columns.
            elif isinstance(action.change, ListMove):
                if phase is PRE:
                    self.beginMoveColumns(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                        QtCore.QModelIndex(),
                        action.change.target_index,
                    )
                if phase is POST:
                    self.endMoveColumns()

            # Change columns.
            elif isinstance(action.change, ListUpdate):
                if phase is POST:
                    self.headerDataChanged.emit(
                        QtCore.Qt.Horizontal,
                        action.change.index,
                        action.change.last_index,
                    )
                    obj_count = len(self.obj() or ())
                    if obj_count:
                        self.dataChanged.emit(
                            self.index(
                                0,
                                action.change.index,
                                QtCore.QModelIndex(),
                            ),
                            self.index(
                                obj_count - 1,
                                action.change.last_index,
                                QtCore.QModelIndex(),
                            ),
                        )

    def _onHeadersObjChanged(self, obj, old_obj, phase):
        """
        **virtual method**

        Called when the headers object changes.

        This method is called *before* the
        :attr:`objettoqt.models.OQListModel.headersObjChanged` signal gets emitted.

        :param obj: New headers list object (or None).
        :type obj: objetto.objects.ListObject or None

        :param old_obj: Old headers list object (or None).
        :type old_obj: objetto.objects.ListObject or None

        :param phase: Phase.
        :type phase: objetto.bases.Phase
        """

    def _onHeadersActionReceived(self, action, phase):
        """
        **virtual method**

        Called when an action is received from the headers object.

        This method is called *before* the
        :attr:`objettoqt.models.OQListModel.headersActionReceived` signal gets emitted.

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: objetto.bases.Phase
        """

    def headersObj(self):
        """
        **final method**

        Get the headers object being observed.

        :return: Headers object being observed.
        :rtype: objetto.objects.ListObject
        """
        return self.__headers.obj()

    def setHeadersObj(self, obj):
        """
        **final method**

        Set the headers object to observe.

        :param obj: Headers object to observe (or None for default).
        :type obj: objetto.objects.ListObject or None
        """
        if obj is None:
            self.__headers.setObj(self.__default_headers_obj)
        else:
            with ReraiseContext(TypeError, "'obj' parameter"):
                assert_is_instance(obj, ListObject)
            for header in obj:
                with ReraiseContext(TypeError, "'obj' parameter contents"):
                    assert_is_instance(header, AbstractListModelHeader)
            self.__headers.setObj(obj)

    def headersObjToken(self):
        """
        **final method**

        Get the action observer token for the headers object.

        :return: Action observer token for the headers object.
        :rtype: objetto.observers.ActionObserverToken
        """
        return self.__headers.objToken()

    def headers(self):
        """
        **final method**

        Get headers.

        :return: Headers.
        :rtype: tuple[objettoqt.models.AbstractListModelHeader]
        """
        return tuple(self.__headers.obj())

    def setHeaders(self, headers=None):
        """
        **final method**

        Set headers.

        :param headers: Headers (or None for default).
        :type headers: collections.abc.Iterable[\
objettoqt.models.AbstractListModelHeader or str] or None
        """
        filtered_headers = []
        for header in headers or ():
            if isinstance(header, string_types):
                header = ListModelHeader(title=header)
            else:
                with ReraiseContext(TypeError, "'headers' parameter contents"):
                    assert_is_instance(header, (AbstractListModelHeader, string_types))
            filtered_headers.append(header)
        if filtered_headers:
            headers_obj = type(self).__default_headers_cls(
                Application(), filtered_headers or (ListModelHeader(),)
            )
        else:
            headers_obj = self.__default_headers_obj
        self.__headers.setObj(headers_obj)

    def index(self, row, column=0, parent=QtCore.QModelIndex(), *args, **kwargs):
        """
        Get index.

        :param row: Row.
        :type row: int

        :param column: Column.
        :type column: int

        :param parent: Parent index.
        :type parent: QtCore.QModelIndex

        :return: Index.
        :rtype: QtCore.QModelIndex
        """
        if not parent.isValid():
            obj = self.obj()
            if obj is not None and 0 <= row < len(obj):
                return self.createIndex(row, column, self.obj()[row])
        return QtCore.QModelIndex()

    def parent(self, index=QtCore.QModelIndex(), *args, **kwargs):
        """
        Get invalid parent index (no valid parent indexes in a list model).

        :return: Invalid parent index.
        :rtype: QtCore.QModelIndex
        """
        return QtCore.QModelIndex()

    def headerData(
        self,
        column=None,
        orientation=QtCore.Qt.Horizontal,
        role=QtCore.Qt.DisplayRole,
        *args,
        **kwargs
    ):
        """
        Get header data.

        :param column: Column.
        :type column: int or None

        :param orientation: Orientation.
        :type orientation: QtCore.Qt.Orientation

        :param role: Role.
        :type role: QtCore.Qt.ItemDataRole

        :return: Header data.
        """
        if orientation == QtCore.Qt.Horizontal:
            headers_obj = self.headersObj()
            with headers_obj.app.read_context():
                if column is None:
                    if len(headers_obj):
                        column = 0
                    else:
                        return None
                if role == QtCore.Qt.DisplayRole:
                    return self.headersObj()[column].title.capitalize()
                elif role == QtCore.Qt.UserRole:
                    return self.headersObj()[column]

    def columnCount(self, *args, **kwargs):
        """
        Get column count.

        :return: Column count.
        :rtype: int
        """
        return len(self.headersObj())

    def rowCount(self, parent=QtCore.QModelIndex(), *args, **kwargs):
        """
        Get value count (row count).

        :return: Value count (row count).
        :rtype: int
        """
        obj = self.obj()
        if obj is None:
            return 0
        return len(obj)

    def flags(self, index=QtCore.QModelIndex(), *args, **kwargs):
        """
        Get flags.

        :param index: Index.
        :type index: QtCore.QModelIndex

        :return: Flags.
        :rtype: QtCore.Qt.ItemFlag
        """
        obj = self.obj()
        if obj is None:
            return QtCore.Qt.NoItemFlags

        row = index.row()
        column = index.column()

        header = self.headersObj()[column]
        flags = header.flags(obj, row)
        flags |= QtCore.Qt.ItemNeverHasChildren

        mime_type = self.mimeType()
        if mime_type:
            flags |= QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        return flags

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        """
        Get data.

        :param index: Index.
        :type index: QtCore.QModelIndex

        :param role: Role.
        :type role: QtCore.Qt.ItemDataRole

        :return: Data.
        """
        obj = self.obj()
        if obj is None:
            return
        row = index.row()
        column = index.column()
        header = self.headersObj()[column]
        return header.data(obj, row, role)

    def mimeType(self):
        """
        Get mime type.

        :return: Mime type.
        :rtype: str or None
        """
        return self.__mime_type

    def mimeTypes(self):
        """
        Get mime types.

        :return: Mime types.
        :rtype: list[str]
        """
        if self.__mime_type:
            return [self.__mime_type]
        return []

    def mimeData(self, indexes):
        """
        Get mime data stream.

        :param indexes: Indexes.
        :type indexes: collections.abc.Iterable[QtCore.QModelIndex]

        :return: Mime data stream.
        :rtype: QtCore.QMimeData or None
        """
        if not indexes:
            return None

        obj = self.obj()
        if obj is None:
            return None

        mime_type = self.mimeType()
        if not mime_type:
            return None

        # Force first column only.
        filtered_indexes = []
        for index in indexes:
            if index.column() != 0:
                index = index.sibling(index.row(), 0)
            filtered_indexes.append(index)

        if not filtered_indexes:
            return None
        indexes = filtered_indexes

        # Only sequential indexes are supported.
        rows = []
        for i, index in enumerate(sorted(indexes, key=lambda x: x.row())):
            row = index.row()
            if i > 0:
                previous_row = rows[-1]
                if previous_row == row:
                    continue
                if previous_row + 1 != row:
                    return None
            rows.append(row)
        first_row = rows[0]
        last_row = rows[-1]

        serialized_objs = []
        contents = {
            "obj_id": id(obj),
            "first_row": first_row,
            "last_row": last_row,
            "serialized_objs": serialized_objs,
        }
        with obj.app.read_context():
            for row in rows:
                item = obj[row]
                if isinstance(item, BaseObject):
                    try:
                        serialized_obj = item.serialize()
                    except SerializationError:
                        serialized_obj = item
                else:
                    serialized_obj = item
                serialized_objs.append(serialized_obj)

        # Prepare data stream.
        try:
            data_stream = safe_dump(contents)
        except YAMLError:
            return None
        mime_data = QtCore.QMimeData()
        # noinspection PyTypeChecker
        mime_data.setData(mime_type, ensure_binary(data_stream))
        return mime_data

    def supportedDropActions(self):
        """
        Get supported drop actions.

        :return: Supported drop actions.
        :rtype: QtCore.Qt.DropAction
        """
        obj = self.obj()
        if obj is None:
            actions = QtCore.Qt.IgnoreAction
        else:
            mime_type = self.mimeType()
            if mime_type and isinstance(obj, MutableListObject):
                actions = QtCore.Qt.CopyAction | QtCore.Qt.MoveAction
            else:
                actions = QtCore.Qt.IgnoreAction
        return actions

    def supportedDragActions(self):
        """
        Get supported drag actions.

        :return: Supported drag actions.
        :rtype: QtCore.Qt.DropAction
        """
        obj = self.obj()
        if obj is None:
            actions = QtCore.Qt.IgnoreAction
        else:
            mime_type = self.mimeType()
            if mime_type:
                actions = QtCore.Qt.CopyAction
                if isinstance(obj, MutableListObject):
                    actions |= QtCore.Qt.MoveAction
            else:
                actions = QtCore.Qt.IgnoreAction
        return actions

    def dropMimeData(self, data, action, row, column, parent=QtCore.QModelIndex()):
        """
        Handle dropped mime data stream.

        :param data: Mime data stream.
        :type data: QtCore.QMimeData

        :param action: Drop action.
        :type action: QtCore.Qt.DropAction

        :param row: Row.
        :type row: int

        :param column: Column.
        :type column: int

        :param parent: Parent index.
        :type parent: QtCore.QModelIndex

        :return: True if handled it.
        :rtype: bool
        """
        obj = self.obj()
        if obj is None:
            return False
        if not isinstance(obj, MutableListObject):
            return False

        mime_type = self.mimeType()
        if not mime_type:
            return False

        # Prevent dropping on top of an item (only allows in-between items).
        while parent.isValid():
            row, _, parent = parent.row(), parent.column(), parent.parent()

        if row == -1:
            row = len(obj)
        try:
            if action in (QtCore.Qt.CopyAction, QtCore.Qt.MoveAction):

                # Deserialize yaml data.
                data = data.data(mime_type).data()
                data_stream = data.decode("utf8")
                contents = safe_load(data_stream)
                if isinstance(contents, collections_abc.Mapping):
                    try:
                        obj_id = contents["obj_id"]
                        first_row = contents["first_row"]
                        last_row = contents["last_row"]
                        serialized_objs = contents["serialized_objs"]
                    except KeyError:
                        raise TypeError()
                else:
                    raise TypeError()

                # We have results
                if serialized_objs:

                    # Internal move.
                    if action == QtCore.Qt.MoveAction and obj_id == id(obj):
                        if row == last_row + 1:
                            row += 1
                        if not (first_row <= row <= last_row + 1):
                            self.obj().move(slice(first_row, last_row + 1), row)
                            return True

                    # External or copy.
                    else:
                        objs = []
                        subject_obj = self.obj()
                        if subject_obj is not None:
                            with subject_obj.app.write_context():
                                for serialized_obj in serialized_objs:
                                    try:
                                        deserialized_obj = type(
                                            subject_obj
                                        ).deserialize_value(
                                            serialized_obj, None, app=subject_obj.app
                                        )
                                    except SerializationError:
                                        objs = []
                                        break
                                    objs.append(deserialized_obj)
                            if objs:
                                self.obj().insert(row, *objs)
                                return True

        except (YAMLError, TypeError):
            pass
        return False

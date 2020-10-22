# -*- coding: utf-8 -*-

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc

from six import ensure_binary, string_types

from abc import abstractmethod
from PySide2 import QtCore
from yaml import safe_dump, safe_load, YAMLError
from typing import Any, Optional, Tuple, Dict, List, Union, Iterable
from objetto.applications import Application
from objetto.actions import Action, Phase
from objetto.objects import Object, list_object_cls
from objetto.bases import BaseObject, ListObject, MutableListObject
from objetto.exceptions import SerializationError
from objetto.data import InteractiveData, data_attribute
from objetto.utils.type_checking import assert_is_instance
from objetto.changes import (
    ListInsert,
    ListDelete,
    ListMove,
    ListUpdate,
)

from .._mixins.mixin import OQObjectMixin
from .._objects.object import OQObject

__all__ = [
    "BaseListModelHeader",
    "ListModelHeader",
    "DefaultListModelHeader",
    "OQListModel",
]


class BaseListModelHeader(InteractiveData):
    """Carries information on how the data should be retrieved for a column."""
    title = data_attribute(str)  # type: str
    metadata = data_attribute((), default=None)

    def flags(self, obj, row):
        # type: (ListObject, int) -> int
        """Retrieve flags for an item at a specific row."""
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    @abstractmethod
    def data(self, obj, row, role=QtCore.Qt.DisplayRole):
        # type: (ListObject, int, int) -> Any
        """Retrieve data for an item at a specific row."""
        raise NotImplementedError()


class ListModelHeader(BaseListModelHeader):

    def data(self, obj, row, role=QtCore.Qt.DisplayRole):
        # type: (ListObject, int, int) -> Any
        """Retrieve data for an item at a specific row."""
        if role == QtCore.Qt.DisplayRole:
            sub_obj = obj[row]  # type: Object
            return str(sub_obj[self.title])
        elif role == QtCore.Qt.UserRole:
            return obj[row]


class DefaultListModelHeader(BaseListModelHeader):
    """Default list model header (coerces the item to a string for display purposes)."""
    title = data_attribute(str, default="")  # type: str

    def data(self, obj, row, role=QtCore.Qt.DisplayRole):
        # type: (ListObject, int, int) -> Any
        """Retrieve data for an item at a specific row."""
        if role == QtCore.Qt.DisplayRole:
            return str(obj[row])
        elif role == QtCore.Qt.UserRole:
            return obj[row]


class _InternalHeaders(OQObject):

    def _onObjChanged(self, obj, old_obj, phase):
        # type: (Optional[BaseObject], Optional[BaseObject], Phase) -> None
        list_model = self.parent()
        assert isinstance(list_model, OQListModel)
        list_model._onHeadersObjChanged(obj, old_obj, phase)

    def _onActionReceived(self, action, phase):
        # type: (Action, Phase) -> None
        list_model = self.parent()
        assert isinstance(list_model, OQListModel)
        list_model._onActionReceived(action, phase)


class OQListModel(OQObjectMixin, QtCore.QAbstractItemModel):
    """List model."""

    __default_headers_cls = list_object_cls(
        BaseListModelHeader, exact=False, child=False
    )

    def __init__(
        self,
        headers=None,  # type: Optional[Iterable[Union[BaseListModelHeader, str]]]
        mime_type=None,  # type: Optional[str]
        **kwargs
    ):
        # type: (...) -> None
        """Initialize with optional headers and mime type."""
        super(OQListModel, self).__init__(**kwargs)

        self.__headers = _InternalHeaders(parent=self)
        self.__mime_type = mime_type or None

        filtered_headers = []
        for header in headers or ():
            if isinstance(header, string_types):
                header = ListModelHeader(title=header)
            else:
                assert_is_instance(header, BaseListModelHeader, usecase="header type")
            filtered_headers.append(header)
        self.__default_headers_obj = type(self).__default_headers_cls(
            Application(), filtered_headers or (DefaultListModelHeader(),)
        )
        self.__headers.setObj(self.__default_headers_obj)

    def _onObjChanged(self, obj, old_obj, phase):
        if phase is Phase.PRE:
            self.beginResetModel()
        elif phase is Phase.POST:
            self.endResetModel()

    def _onActionReceived(self, action, phase):

        # The list changed.
        if action.sender is self.obj():

            # Insert rows.
            if isinstance(action.change, ListInsert):
                if phase is Phase.PRE:
                    self.beginInsertRows(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                elif phase is Phase.POST:
                    self.endInsertRows()

            # Delete rows.
            elif isinstance(action.change, ListDelete):
                if phase is Phase.PRE:
                    self.beginRemoveRows(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                elif phase is Phase.POST:
                    self.endRemoveRows()

            # Move rows.
            elif isinstance(action.change, ListMove):
                if phase is Phase.PRE:
                    self.beginMoveRows(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                        QtCore.QModelIndex(),
                        action.change.target_index,
                    )
                elif phase is Phase.POST:
                    self.endMoveRows()

            # Change rows.
            elif isinstance(action.change, ListUpdate):
                if phase is Phase.POST:
                    self.dataChanged.emit(
                        self.index(action.change.index, 0, QtCore.QModelIndex()),
                        self.index(
                            action.change.last_index,
                            self.columnCount() - 1,
                            QtCore.QModelIndex(),
                        ),
                    )

    def _onHeadersObjChanged(self, obj, old_obj, phase):
        if old_obj is not None:
            if phase is Phase.PRE:
                self.beginResetModel()
            elif phase is Phase.POST:
                self.endResetModel()

    def _onHeadersActionReceived(self, action, phase):

        # The headers changed.
        if action.sender is self.__headers.obj():

            # Insert columns.
            if isinstance(action.change, ListInsert):
                if phase is Phase.PRE:
                    self.beginInsertColumns(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                elif phase is Phase.POST:
                    self.endInsertColumns()

            # Delete columns.
            elif isinstance(action.change, ListDelete):
                if phase is Phase.PRE:
                    self.beginRemoveColumns(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                    )
                if phase is Phase.POST:
                    self.endRemoveColumns()

            # Move columns.
            elif isinstance(action.change, ListMove):
                if phase is Phase.PRE:
                    self.beginMoveColumns(
                        QtCore.QModelIndex(),
                        action.change.index,
                        action.change.last_index,
                        QtCore.QModelIndex(),
                        action.change.target_index,
                    )
                if phase is Phase.POST:
                    self.endMoveColumns()

            # Change columns.
            elif isinstance(action.change, ListUpdate):
                if phase is Phase.POST:
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

    def headersObj(self):
        """Get headers list object."""
        return self.__headers.obj()

    def setHeadersObj(self, obj):
        """Set headers list object."""
        if obj is None:
            self.__headers.setObj(self.__default_headers_obj)
        else:
            assert_is_instance(obj, ListObject, usecase="'obj' parameter")
            for header in obj:
                assert_is_instance(header, BaseListModelHeader, usecase="header type")
            self.__headers.setObj(obj)

    def headersObjToken(self):
        """Get headers list object token."""
        return self.__headers.objToken()

    def headers(self):
        """Get headers."""
        return tuple(self.__headers.obj())

    def setHeaders(self, headers=None):
        # type: (Optional[Iterable[Union[BaseListModelHeader, str]]]) -> None
        """Set headers."""
        filtered_headers = []
        for header in headers or ():
            if isinstance(header, string_types):
                header = ListModelHeader(title=header)
            else:
                assert_is_instance(header, BaseListModelHeader, usecase="header type")
            filtered_headers.append(header)
        if filtered_headers:
            headers_obj = type(self).__default_headers_cls(
                Application(), filtered_headers or (DefaultListModelHeader(),)
            )
        else:
            headers_obj = self.__default_headers_obj
        self.__headers.setObj(headers_obj)

    def index(
        self,
        row,  # type: int
        column=0,  # type: int
        parent=QtCore.QModelIndex(),  # type: QtCore.QModelIndex
        *args,
        **kwargs
    ):
        # type: (...) -> QtCore.QModelIndex
        """Make QModelIndex."""
        if not parent.isValid():
            obj = self.obj()
            if obj is not None and 0 <= row < len(obj):
                return self.createIndex(row, column, self.obj()[row])
        return QtCore.QModelIndex()

    def parent(self, index=QtCore.QModelIndex()):
        # type: (QtCore.QModelIndex) -> QtCore.QModelIndex
        """Get invalid parent index (no valid parent indexes in a list model)."""
        return QtCore.QModelIndex()

    def headerData(self, column, orientation, role=QtCore.Qt.DisplayRole):
        # type: (int, int, int) -> Any
        """Get header data."""
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self.headersObj()[column].title
            elif role == QtCore.Qt.UserRole:
                return self.headersObj()[column]

    def columnCount(self, *args, **kwargs):
        # type: (Tuple[Any, ...], Dict[str, Any]) -> int
        """Get column count."""
        return len(self.headersObj())

    def rowCount(self, parent=QtCore.QModelIndex(), *args, **kwargs):
        # type: (QtCore.QModelIndex, Tuple[Any, ...], Dict[str, Any]) -> int
        """Get value count."""
        obj = self.obj()
        if obj is None:
            return 0
        return len(obj)

    def flags(self, index=QtCore.QModelIndex):
        # type: (QtCore.QModelIndex) -> int
        """Get flags."""
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
        # type: (QtCore.QModelIndex, int) -> Any
        """Get data."""
        obj = self.obj()
        if obj is None:
            return
        row = index.row()
        column = index.column()
        header = self.headersObj()[column]
        return header.data(obj, row, role)

    def mimeType(self):
        # type: () -> Optional[str]
        """Get mime type."""
        return self.__mime_type

    def mimeTypes(self):
        # type: () -> List[str]
        """Get mime types."""
        if self.__mime_type:
            return [self.__mime_type]
        return []

    def mimeData(self, indexes):
        # type: (List[QtCore.QModelIndex]) -> Optional[QtCore.QMimeData]
        """Get mime data."""
        if not indexes:
            return None

        obj = self.obj()
        if obj is None:
            return None

        mime_type = self.mimeType()
        if not mime_type:
            return None

        # Remove redundant indexes (columns other than 0).
        indexes = filter(lambda idx: idx.column() == 0, indexes)
        if not indexes:
            return None

        # Only sequential indexes are supported.
        rows = []
        for i, index in enumerate(sorted(indexes, key=lambda i: i.row())):
            row = index.row()
            if i > 0:
                previous_row = rows[-1]
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
        mime_data.setData(mime_type, ensure_binary(data_stream))
        return mime_data

    def supportedDropActions(self):
        # type: () -> int
        """Supported drop actions."""
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
        # type: () -> int
        """Supported drag actions."""
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

    def dropMimeData(
        self,
        data,  # type: QtCore.QMimeData
        action,  # type: int
        row,  # type: int
        column,  # type: int
        parent=QtCore.QModelIndex()  # type: QtCore.QModelIndex
    ):
        # type: (...) -> bool
        """Mime data was dropped."""
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
            row, column, parent = parent.row(), parent.column(), parent.parent()

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

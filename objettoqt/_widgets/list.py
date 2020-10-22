# -*- coding: utf-8 -*-
"""Qt list widgets."""

from PySide2 import QtWidgets, QtCore
from weakref import WeakKeyDictionary, WeakValueDictionary
from objetto.actions import Phase
from objetto.changes import ListInsert, ListMove
from typing import TYPE_CHECKING
from six.moves import xrange as x_range

from .._mixins.mixin import OQObjectMixin
from .._models.list import OQListModel
from .._views.list import OQListView

if TYPE_CHECKING:
    from typing import Type, Optional, Tuple, Callable

__all__ = ["OQWidgetList"]


class _OQWidgetListModel(OQListModel):

    def setObj(self, obj):
        self.parent().setObj(obj)

    def data(self, *args, **kwargs):
        return


class OQWidgetList(OQObjectMixin, OQListView):
    """List of widgets."""

    def __init__(
        self,
        editor_widget_type,  # type: Type[OQObjectMixin]
        mime_type=None,  # type: Optional[str]
        scrollable=True,  # type: bool
        context_menu_callback=None,  # type: Optional[Callable]
        **kwargs
    ):
        # type: (...) -> None
        super(OQWidgetList, self).__init__(**kwargs)

        self.__editor_widget_type = editor_widget_type
        self.__scrollable = bool(scrollable)
        self.__delegate = _WidgetListDelegate(parent=self)
        self.__model = _OQWidgetListModel(mime_type=mime_type, parent=self)
        self.__context_menu_callback = context_menu_callback

        self.installEventFilter(self)
        self.viewport().installEventFilter(self)

        if not scrollable:
            super(OQWidgetList, self).setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
            super(OQWidgetList, self).setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
            super(OQWidgetList, self).setFixedHeight(0)

        super(OQWidgetList, self).setUniformItemSizes(False)
        super(OQWidgetList, self).setItemDelegate(self.__delegate)
        super(OQWidgetList, self).setModel(self.__model)

    def __updateLayout__(self):
        if not self.__scrollable:
            height = 4
            for widget in self.editors() or ():
                height += widget.sizeHint().height()
            super(OQWidgetList, self).setFixedHeight(height)
        self.__model.layoutChanged.emit()

    def _onObjChanged(self, obj, old_obj, phase):
        if phase is Phase.PRE:
            super(_OQWidgetListModel, self.__model).setObj(None)
        elif phase is Phase.POST:
            super(_OQWidgetListModel, self.__model).setObj(obj)
            for i, value in enumerate(obj):
                self.openPersistentEditor(self.__model.index(i))

    def _onActionReceived(self, action, phase):
        if action.sender is self.__model.obj() and phase is Phase.POST:

            # Wait for the model to receive it first.
            self.__model.objToken().wait()

            # Open persistent editors when items are inserted.
            if isinstance(action.change, ListInsert):
                self.clearSelection()
                indexes = []
                for i in x_range(action.change.index, action.change.last_index + 1):
                    index = self.__model.index(i, 0, QtCore.QModelIndex())
                    self.openPersistentEditor(index)
                    indexes.append(index)

                if indexes:
                    if len(indexes) > 1:
                        self.select(
                            QtCore.QItemSelection(indexes[0], indexes[-1]),
                            QtCore.QItemSelectionModel.Select,
                            indexes[-1]
                        )
                    else:
                        self.select(
                            indexes[0], QtCore.QItemSelectionModel.Select, indexes[0]
                        )

            # Select moved items.
            elif isinstance(action.change, ListMove):
                first = self.__model.index(
                    action.change.post_index, 0, QtCore.QModelIndex()
                )
                if action.change.post_index != action.change.post_last_index:
                    last = self.__model.index(
                        action.change.post_last_index, 0, QtCore.QModelIndex()
                    )
                    selection = QtCore.QItemSelection(first, last)
                    current = last
                else:
                    selection = first
                    current = first
                self.select(
                    selection, QtCore.QItemSelectionModel.ClearAndSelect, current
                )

    def setItemDelegate(self, value):
        error = "can't set item delegate on '{}' object".format(type(self).__name__)
        raise RuntimeError(error)

    def setModel(self, value):
        error = "can't set model on '{}' object".format(type(self).__name__)
        raise RuntimeError(error)

    def setUniformItemSizes(self, value):
        error = "can't set uniform item size on '{}' object".format(type(self).__name__)
        raise RuntimeError(error)

    def setHorizontalScrollBarPolicy(self, value):
        if not self.__scrollable:
            error = "can't set horizontal scrollbar policy on a non-scrollable list"
            raise RuntimeError(error)
        super(OQWidgetList, self).setHorizontalScrollBarPolicy(value)

    def setVerticalScrollBarPolicy(self, value):
        if not self.__scrollable:
            error = "can't set vertical scrollbar policy on a non-scrollable list"
            raise RuntimeError(error)
        super(OQWidgetList, self).setVerticalScrollBarPolicy(value)

    def setFixedHeight(self, value):
        if not self.__scrollable:
            error = "can't set fixed height on a non-scrollable list"
            raise RuntimeError(error)
        super(OQWidgetList, self).setFixedHeight(value)

    def scrollable(self):
        # type: () -> bool
        """Get whether this list is scrollable."""
        return self.__scrollable

    def editors(self):
        # type: () -> Tuple[OQObjectMixin, ...]
        """Get editor widgets."""
        obj = self.obj()
        if not obj:
            return ()
        editors = []
        for value in obj:
            widget = self.itemDelegate().getEditor(value)
            if widget is None:
                return ()
            editors.append(widget)
        return tuple(editors)

    def resizeEvent(self, event):
        super(OQWidgetList, self).resizeEvent(event)
        self.__model.layoutChanged.emit()

    def editorWidgetType(self):
        """Get editor widget type."""
        return self.__editor_widget_type

    def mimeType(self):
        """Get mime type."""
        return self.__mime_type


class _WidgetListDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent):
        super(_WidgetListDelegate, self).__init__(parent=parent)
        self.__editors = WeakValueDictionary()
        self.__sizes = WeakKeyDictionary()
        self.__size_hints = WeakKeyDictionary()

    def createEditor(self, parent, option, index):
        widget = self.parent()
        if widget is not None:
            obj = widget.obj()
            if obj is not None:
                editor = widget.editorWidgetType()()
                editor.setParent(parent)
                value = obj[index.row()]
                editor.setObj(value)
                self.__editors[id(value)] = editor
                self.__sizes[editor] = editor.size()
                self.__size_hints[editor] = editor.sizeHint()
                return editor
        return QtWidgets.QLabel(parent=parent)

    def setEditorData(self, editor, index):
        widget = self.parent()
        if widget is not None:
            obj = widget.obj()
            if obj is not None:
                old_value = editor.obj()
                new_value = obj[index.row()]
                if old_value is not new_value:
                    self.__editors.pop(id(old_value), None)
                    self.__editors[id(new_value)] = editor
                    editor.setObj(new_value)
                    widget.__updateLayout__()

    def sizeHint(self, option, index):
        widget = self.parent()
        if widget is not None:
            obj = widget.obj()
            if obj is not None:
                row = index.row()
                value = obj[row]
                value_id = id(value)
                editor = self.__editors.get(value_id, None)
                if editor is not None:
                    size_hint = editor.sizeHint()
                    size = editor.size()
                    previous_size = self.__sizes[editor]
                    previous_size_hint = self.__size_hints[editor]
                    if size != previous_size:
                        self.__sizes[editor] = size
                    if size_hint != previous_size_hint:
                        self.__size_hints[editor] = size_hint
                    if size_hint != previous_size_hint or size != previous_size:
                        widget.__updateLayout__()
                    return size_hint
        return QtCore.QSize(0, 0)

    def getEditor(self, value):
        return self.__editors.get(id(value))

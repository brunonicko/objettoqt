# -*- coding: utf-8 -*-
"""Qt list widgets."""

from PySide2 import QtWidgets, QtCore, QtGui
from weakref import WeakKeyDictionary, WeakValueDictionary
from objetto.objects import ListObject, MutableListObject
from objetto.actions import Phase
from objetto.changes import ListInsert, ListMove
from typing import TYPE_CHECKING
from six.moves import xrange as x_range

from .._mixins.mixin import OQObjectMixin
from .._models.list import OQListModel
from .._views.list import OQListView

if TYPE_CHECKING:
    from typing import Any, Type, Optional, Union, Tuple, Callable

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

        self.__mouse_lock = None
        self.__drag_start_pos = None
        self.__drag_start_indexes = None
        self.__nav_start_pos = None

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
            height = 2
            for widget in self.editors() or ():
                height += widget.sizeHint().height()
            self.setFixedHeight(height)
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

    @QtCore.Slot()
    def deleteSelected(self):
        obj = self.obj()
        if isinstance(obj, MutableListObject):
            selected_rows = sorted(
                (i.row() for i in self.selectedIndexes()), reverse=True
            )
            if selected_rows:
                first_index = min(selected_rows)
                last_index = max(selected_rows)
                obj.delete_slice(slice(first_index, last_index + 1))

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

    def select(
        self,
        selection,  # type: Union[QtCore.QModelIndex, QtCore.QItemSelection]
        mode,  # type: int
        current=None  # type: Optional[QtCore.QModelIndex]
    ):
        # type: (...) -> None
        """Select and set current."""
        selection_model = self.selectionModel()
        if selection_model is None:
            return
        if current is not None:
            selection_model.setCurrentIndex(
                current, QtCore.QItemSelectionModel.NoUpdate
            )
        else:
            selection_model.clearCurrentIndex()
        selection_model.select(selection, mode)

    @QtCore.Slot()
    def clearSelection(self):
        # type: () -> None
        """Clear selection and current."""
        selection_model = self.selectionModel()
        if selection_model is None:
            return
        self.selectionModel().clearSelection()
        self.selectionModel().clearCurrentIndex()

    def showCustomContextMenu(self):
        """Show custom context menu."""
        if self.__context_menu_callback is not None:
            return self.__context_menu_callback(self)
        return False

    def eventFilter(self, obj, event):
        # type: (OQListView, Union[QtCore.QEvent, Any]) -> bool
        """Override default behaviors."""

        # Object is the list view.
        if obj is self:

            # Pressed delete, is enabled and has focus, delete selected.
            if (
                event.type() == QtCore.QEvent.KeyPress
                and event.key() == QtCore.Qt.Key_Delete
                and self.hasFocus()
                and self.isEnabled()
            ):
                event.accept()
                if self.__mouse_lock is None:
                    self.deleteSelected()
                return True

        # Object is the viewport.
        elif obj is self.viewport():

            # Mouse wheel event.
            if event.type() == QtCore.QEvent.Wheel:

                # Locked.
                if self.__mouse_lock is not None:
                    event.accept()
                    return True

                # If the view can't be scrolled, pass through.
                cannot_scroll = bool(
                    self.horizontalScrollBar().minimum()
                    == self.horizontalScrollBar().maximum()
                    and self.verticalScrollBar().minimum()
                    == self.verticalScrollBar().maximum()
                )
                if cannot_scroll:
                    event.ignore()
                    return False

                # Accept event.
                event.accept()

                # Get delta.
                delta = QtCore.QPointF(event.angleDelta()) * 0.3

                # Fix orientation.
                if (
                    self.horizontalScrollBar().minimum()
                    == self.horizontalScrollBar().maximum()
                    and delta.y() == 0
                    and delta.x() != 0
                ) or (
                    self.verticalScrollBar().minimum()
                    == self.verticalScrollBar().maximum()
                    and delta.x() == 0
                    and delta.y() != 0
                ):
                    delta = QtCore.QPoint(delta.y(), delta.x())

                # Get current scroll values.
                scroll_x = self.horizontalScrollBar().value()
                scroll_y = self.verticalScrollBar().value()

                # Increment them with the delta.
                self.horizontalScrollBar().setValue(scroll_x - delta.x())
                self.verticalScrollBar().setValue(scroll_y - delta.y())

                return True

            # Button was pressed down.
            if event.type() == QtCore.QEvent.MouseButtonPress:

                # Already locked.
                if self.__mouse_lock is not None:
                    return True

                # Lock mouse.
                self.__mouse_lock = event.button()

                # Alt modifier or mid button, check if we can navigate.
                if (
                    event.modifiers() & QtCore.Qt.AltModifier
                    or event.button() == QtCore.Qt.MidButton
                ):

                    # Can't scroll, cancel.
                    cannot_scroll = bool(
                        self.horizontalScrollBar().minimum()
                        == self.horizontalScrollBar().maximum()
                        and self.verticalScrollBar().minimum()
                        == self.verticalScrollBar().maximum()
                    )
                    if cannot_scroll:
                        self.__mouse_lock = None
                        event.ignore()
                        return True

                    # Start navigation.
                    QtWidgets.QApplication.instance().setOverrideCursor(
                        QtCore.Qt.ClosedHandCursor
                    )
                    self.__nav_start_pos = event.pos()
                    return True

                # Left button click.
                if event.button() == QtCore.Qt.LeftButton:

                    # If we can modify the list.
                    if isinstance(self.obj(), ListObject) and self.isEnabled():

                        # Get selected indexes.
                        selected_indexes = self.selectedIndexes()

                        # Get index under the mouse.
                        index = self.indexAt(event.pos())

                        # Start waiting for dragging.
                        if index.isValid():
                            event.accept()
                            self.__drag_start_pos = event.pos()
                            if index in selected_indexes:
                                self.__drag_start_indexes = selected_indexes
                            else:
                                self.__drag_start_indexes = [index]
                            return True

                    # Fix selection not being contiguous.
                    self.clearSelection()
                    return True

                # Right button click.
                if event.button() == QtCore.Qt.RightButton:
                    event.accept()

                    # Resolve selection.
                    index = self.indexAt(event.pos())
                    selected_indexes = self.selectedIndexes()
                    if index and index.isValid() and index not in selected_indexes:
                        self.select(
                            index, QtCore.QItemSelectionModel.ClearAndSelect, index
                        )
                    elif not index or not index.isValid():
                        self.clearSelection()

                    # Request context menu.
                    menu_shown = self.showCustomContextMenu()

                    # Release lock if menu shown.
                    if menu_shown:
                        self.__mouse_lock = None

                    return True

            # Mouse is moving.
            elif event.type() == QtCore.QEvent.MouseMove:

                # There's no lock, pass-through.
                if self.__mouse_lock is None:
                    event.ignore()
                    return True

                # If locked button is not present, do nothing.
                if not (int(event.buttons()) & self.__mouse_lock):
                    return True

                # Update navigation.
                if self.__nav_start_pos is not None:

                    # Get delta and reset start position.
                    delta = self.__nav_start_pos - event.pos()
                    self.__nav_start_pos = event.pos()

                    # Get current scroll values.
                    scroll_x = self.horizontalScrollBar().value()
                    scroll_y = self.verticalScrollBar().value()

                    # Increment them with the delta.
                    self.horizontalScrollBar().setValue(
                        scroll_x + delta.x()
                    )
                    self.verticalScrollBar().setValue(scroll_y + delta.y())
                    return True

                # Left button and dragging, update drag.
                if (
                    int(event.buttons())
                    and (int(event.buttons()) & QtCore.Qt.LeftButton)
                    and self.__drag_start_pos is not None
                ):
                    event.accept()

                    distance_point = event.pos() - self.__drag_start_pos
                    distance = distance_point.manhattanLength()
                    drag_distance = (
                        QtWidgets.QApplication.instance().startDragDistance()
                    )

                    # We have enough distance.
                    if distance >= drag_distance:

                        # Select.
                        selected_indexes = self.selectedIndexes()
                        if selected_indexes != self.__drag_start_indexes:
                            if self.__drag_start_indexes:
                                self.__drag_start_indexes = sorted(
                                    self.__drag_start_indexes,
                                    key=lambda i: i.row()
                                )
                                selection = QtCore.QItemSelection(
                                    self.__drag_start_indexes[0],
                                    self.__drag_start_indexes[-1]
                                )
                                if (
                                    self.__drag_start_indexes[0].row() !=
                                    self.__drag_start_indexes[-1].row()
                                ):
                                    self.select(
                                        selection,
                                        QtCore.QItemSelectionModel.ClearAndSelect,
                                        self.__drag_start_indexes[-1]
                                    )
                                else:
                                    self.select(
                                        selection,
                                        QtCore.QItemSelectionModel.ClearAndSelect,
                                        self.__drag_start_indexes[0]
                                    )
                                selected_indexes = self.selectedIndexes()

                        # Reset drag start pos.
                        drag_start_pos = self.__drag_start_pos
                        self.__drag_start_pos = None
                        self.__drag_start_indexes = None

                        # Can we drag?
                        if not self.dragEnabled():
                            return True

                        # Get mime data.
                        mime_data = self.__model.mimeData(selected_indexes)
                        if mime_data is None:
                            return True

                        # Get drag actions.
                        drag_actions = self.__model.supportedDragActions()

                        # Start drag.
                        viewport = self.viewport()
                        drag = QtGui.QDrag(viewport)
                        drag.setMimeData(mime_data)

                        # Prepare pixmap.
                        pixmap = QtGui.QPixmap(
                            viewport.visibleRegion().boundingRect().size()
                        )
                        pixmap.fill(QtCore.Qt.transparent)
                        painter = QtGui.QPainter(pixmap)
                        for index in self.selectedIndexes():
                            painter.drawPixmap(
                                self.visualRect(index),
                                viewport.grab(self.visualRect(index)),
                            )
                        painter.end()
                        drag.setPixmap(pixmap)
                        drag.setHotSpot(drag_start_pos)

                        # Prepare cursor.
                        move_cursor = QtGui.QCursor(QtCore.Qt.DragMoveCursor)
                        copy_cursor = QtGui.QCursor(QtCore.Qt.DragCopyCursor)
                        drag.setDragCursor(move_cursor.pixmap(), QtCore.Qt.MoveAction)
                        drag.setDragCursor(copy_cursor.pixmap(), QtCore.Qt.CopyAction)

                        # Execute drag.
                        try:
                            drag.exec_(drag_actions)
                        finally:
                            self.__mouse_lock = None
                            self.__drag_start_pos = None
                            self.__drag_start_indexes = None
                            self.__nav_start_pos = None

                    return True
                elif not self.__drag_start_indexes:
                    return True

            # Released a button.
            elif event.type() == QtCore.QEvent.MouseButtonRelease:

                # There's no lock, pass-through.
                if self.__mouse_lock is None:
                    event.ignore()
                    return True

                # If not the locked button, do nothing.
                if event.button() != self.__mouse_lock:
                    return True

                # Release lock.
                self.__mouse_lock = None

                # Finish navigation.
                if self.__nav_start_pos is not None:
                    QtWidgets.QApplication.instance().restoreOverrideCursor()
                    self.__nav_start_pos = None

                    return True

                # Left button.
                if event.button() == QtCore.Qt.LeftButton:

                    # Failed to drag, consider this a single click.
                    if self.__drag_start_pos is not None:
                        event.accept()

                        # Reset drag start pos.
                        self.__drag_start_pos = None
                        self.__drag_start_indexes = None

                        # Get index under the mouse and selected indexes.
                        index = self.indexAt(event.pos())
                        selected_indexes = sorted(
                            self.selectedIndexes(),
                            key=lambda i: i.row()
                        )

                        # We have an index under mouse or selected indexes.
                        if (
                            selected_indexes and
                            event.modifiers() == QtCore.Qt.ShiftModifier and
                            index and
                            index.isValid()
                        ):
                            first_selected = selected_indexes[0]
                            last_selected = selected_indexes[-1]

                            # Extending selection below.
                            if index.row() > last_selected.row():
                                first = last_selected.sibling(
                                    last_selected.row() + 1, 0
                                )
                                if first.isValid():
                                    last = index
                                    if last.isValid() and first.row() != last.row():
                                        selection = QtCore.QItemSelection(first, last)
                                        self.select(
                                            selection,
                                            QtCore.QItemSelectionModel.Select,
                                            last
                                        )
                                    else:
                                        self.select(
                                            first,
                                            QtCore.QItemSelectionModel.Select,
                                            first
                                        )

                            # Contracting selection within.
                            elif (
                                first_selected.row() < index.row() < last_selected.row()
                            ):
                                first = index.sibling(index.row() + 1, 0)
                                last = last_selected
                                if last.row() != first.row():
                                    clear_selection = QtCore.QItemSelection(
                                        first, last
                                    )
                                    self.select(
                                        clear_selection,
                                        QtCore.QItemSelectionModel.Deselect,
                                        None
                                    )
                                else:
                                    self.select(
                                        first,
                                        QtCore.QItemSelectionModel.Deselect,
                                        None
                                    )

                            # Extending selection above.
                            elif index.row() < first_selected.row():
                                first = index
                                last = first_selected.sibling(
                                    first_selected.row() - 1, 0
                                )
                                if last.isValid() and first.row() != last.row():
                                    selection = QtCore.QItemSelection(first, last)
                                    self.select(
                                        selection,
                                        QtCore.QItemSelectionModel.Select,
                                        last
                                    )
                                else:
                                    self.select(
                                        first, QtCore.QItemSelectionModel.Select, first
                                    )

                        elif index and index.isValid():
                            self.select(
                                index, QtCore.QItemSelectionModel.ClearAndSelect, index
                            )
                        else:
                            self.clearSelection()

                        return True
        return False


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

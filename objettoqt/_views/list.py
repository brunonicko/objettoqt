# -*- coding: utf-8 -*-

from PySide2 import QtWidgets, QtCore, QtGui
from objetto.bases import MutableListObject

__all__ = ["OQListViewMixin", "OQListView", "OQTreeListView"]


class OQListViewMixin(object):

    def __init__(self, **kwargs):
        super(OQListViewMixin, self).__init__(**kwargs)

        self.__mouse_lock = None
        self.__drag_start_pos = None
        self.__drag_start_indexes = None
        self.__nav_start_pos = None

        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setDropIndicatorShown(False)

        self.installEventFilter(self)
        self.viewport().installEventFilter(self)

    def setSelectionMode(self, mode):
        allowed_modes = (
            QtWidgets.QAbstractItemView.SingleSelection,
            QtWidgets.QAbstractItemView.ContiguousSelection,
            QtWidgets.QAbstractItemView.NoSelection,
        )
        if mode not in allowed_modes:
            error = "selection mode {} is not supported".format(mode)
            raise ValueError(error)
        super(OQListViewMixin, self).setSelectionMode(mode)

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
    def deleteSelected(self):
        if not self.isEnabled():
            return

        model = self.model()
        if model is None:
            return

        obj = model.obj()
        if isinstance(obj, MutableListObject):
            selected_rows = sorted(
                (i.row() for i in self.selectedIndexes()), reverse=True
            )
            if selected_rows:
                first_index = min(selected_rows)
                last_index = max(selected_rows)
                obj.delete_slice(slice(first_index, last_index + 1))

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
        return

    def eventFilter(self, obj, event):
        # type: (QtCore.QObject, Union[QtCore.QEvent, Any]) -> bool
        """Override default behaviors."""

        # Object is the view.
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
                    if self.isEnabled():
                        if self.model() is not None and hasattr(self.model(), "obj"):
                            if isinstance(self.model().obj(), MutableListObject):

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
                        if not self.dragEnabled() or self.model() is None:
                            return True

                        # Get mime data.
                        mime_data = self.model().mimeData(selected_indexes)
                        if mime_data is None:
                            return True

                        # Get drag actions.
                        drag_actions = self.model().supportedDragActions()

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


class OQListView(OQListViewMixin, QtWidgets.QListView):
    """List view."""
    pass


class OQTreeListView(OQListViewMixin, QtWidgets.QTreeView):
    """List view with support for multiple columns."""
    pass

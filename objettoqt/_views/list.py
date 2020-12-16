# -*- coding: utf-8 -*-
"""List view."""

from objetto.objects import MutableListObject
from Qt import QtCore, QtGui, QtWidgets

from .._mixins import OQAbstractItemViewMixin, OQAbstractItemModelMixin

__all__ = ["OQListViewMixin", "OQListView", "OQTreeListView"]


class _OQListViewMixinEventFilter(QtCore.QObject):
    """Internal event filter for `OQListViewMixin`."""

    def __init__(self, list_view):
        self.__mouse_lock = None
        self.__drag_start_pos = None
        self.__drag_start_indexes = None
        self.__nav_start_pos = None

        super(_OQListViewMixinEventFilter, self).__init__(parent=list_view)

    def eventFilter(self, obj, event):

        # Get list view.
        list_view = self.parent()
        if not isinstance(list_view, OQListViewMixin):
            return False

        # Object is the view.
        if obj is list_view:

            # Pressed delete, is enabled and has focus, delete selected.
            if (
                event.type() == QtCore.QEvent.KeyPress
                and event.key() == QtCore.Qt.Key_Delete
                and list_view.hasFocus()
                and list_view.isEnabled()
            ):
                event.accept()
                if self.__mouse_lock is None:
                    list_view.deleteSelected()
                return True

        # Object is the viewport.
        elif obj is list_view.viewport():

            # Mouse wheel event.
            if event.type() == QtCore.QEvent.Wheel:

                # Locked.
                if self.__mouse_lock is not None:
                    event.accept()
                    return True

                # If the view can't be scrolled, pass through.
                cannot_scroll = bool(
                    list_view.horizontalScrollBar().minimum()
                    == list_view.horizontalScrollBar().maximum()
                    and list_view.verticalScrollBar().minimum()
                    == list_view.verticalScrollBar().maximum()
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
                    list_view.horizontalScrollBar().minimum()
                    == list_view.horizontalScrollBar().maximum()
                    and delta.y() == 0
                    and delta.x() != 0
                ) or (
                    list_view.verticalScrollBar().minimum()
                    == list_view.verticalScrollBar().maximum()
                    and delta.x() == 0
                    and delta.y() != 0
                ):
                    delta = QtCore.QPoint(delta.y(), delta.x())

                # Get current scroll values.
                scroll_x = list_view.horizontalScrollBar().value()
                scroll_y = list_view.verticalScrollBar().value()

                # Increment them with the delta.
                list_view.horizontalScrollBar().setValue(scroll_x - delta.x())
                list_view.verticalScrollBar().setValue(scroll_y - delta.y())

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
                        list_view.horizontalScrollBar().minimum()
                        == list_view.horizontalScrollBar().maximum()
                        and list_view.verticalScrollBar().minimum()
                        == list_view.verticalScrollBar().maximum()
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
                    if list_view.isEnabled():
                        model = list_view.model()
                        if isinstance(model, OQAbstractItemModelMixin):
                            if isinstance(model.obj(), MutableListObject):

                                # Get selected indexes.
                                selected_indexes = list_view.selectedIndexes()

                                # Get index under the mouse.
                                index = list_view.indexAt(event.pos())

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
                    list_view.clearSelection()
                    return True

                # Right button click.
                if event.button() == QtCore.Qt.RightButton:
                    event.accept()

                    # Resolve selection.
                    index = list_view.indexAt(event.pos())
                    selected_indexes = list_view.selectedIndexes()
                    if index and index.isValid() and index not in selected_indexes:
                        list_view.select(
                            index, QtCore.QItemSelectionModel.ClearAndSelect, index
                        )
                    elif not index or not index.isValid():
                        list_view.clearSelection()

                    # Request context menu.
                    menu_shown = list_view.showCustomContextMenu(event.pos())

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
                    scroll_x = list_view.horizontalScrollBar().value()
                    scroll_y = list_view.verticalScrollBar().value()

                    # Increment them with the delta.
                    list_view.horizontalScrollBar().setValue(scroll_x + delta.x())
                    list_view.verticalScrollBar().setValue(scroll_y + delta.y())
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
                        selected_indexes = list_view.selectedIndexes()
                        if selected_indexes != self.__drag_start_indexes:
                            if self.__drag_start_indexes:
                                self.__drag_start_indexes = sorted(
                                    self.__drag_start_indexes, key=lambda i: i.row()
                                )
                                selection = QtCore.QItemSelection(
                                    self.__drag_start_indexes[0],
                                    self.__drag_start_indexes[-1],
                                )
                                if (
                                    self.__drag_start_indexes[0].row()
                                    != self.__drag_start_indexes[-1].row()
                                ):
                                    list_view.select(
                                        selection,
                                        QtCore.QItemSelectionModel.ClearAndSelect,
                                        self.__drag_start_indexes[-1],
                                    )
                                else:
                                    list_view.select(
                                        selection,
                                        QtCore.QItemSelectionModel.ClearAndSelect,
                                        self.__drag_start_indexes[0],
                                    )
                                selected_indexes = list_view.selectedIndexes()

                        # Reset drag start pos.
                        drag_start_pos = self.__drag_start_pos
                        self.__drag_start_pos = None
                        self.__drag_start_indexes = None

                        # Can we drag?
                        if not list_view.dragEnabled() or list_view.model() is None:
                            return True

                        # Get mime data.
                        mime_data = list_view.model().mimeData(selected_indexes)
                        if mime_data is None:
                            return True

                        # Get drag actions.
                        drag_actions = list_view.model().supportedDragActions()

                        # Start drag.
                        viewport = list_view.viewport()
                        drag = QtGui.QDrag(viewport)
                        drag.setMimeData(mime_data)

                        # Prepare pixmap.
                        pixmap = QtGui.QPixmap(
                            viewport.visibleRegion().boundingRect().size()
                        )
                        pixmap.fill(QtCore.Qt.transparent)
                        painter = QtGui.QPainter(pixmap)
                        for index in list_view.selectedIndexes():
                            painter.drawPixmap(
                                list_view.visualRect(index),  # TODO: entire row
                                viewport.grab(list_view.visualRect(index)),
                            )
                        painter.end()
                        drag.setPixmap(pixmap)  # TODO: gradient fade
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
                        index = list_view.indexAt(event.pos())
                        selected_indexes = sorted(
                            list_view.selectedIndexes(), key=lambda i: i.row()
                        )

                        # We have an index under mouse or selected indexes.
                        if (
                            selected_indexes
                            and event.modifiers() == QtCore.Qt.ShiftModifier
                            and index
                            and index.isValid()
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
                                        list_view.select(
                                            selection,
                                            QtCore.QItemSelectionModel.Select,
                                            last,
                                        )
                                    else:
                                        list_view.select(
                                            first,
                                            QtCore.QItemSelectionModel.Select,
                                            first,
                                        )

                            # Contracting selection within.
                            elif (
                                first_selected.row() < index.row() < last_selected.row()
                            ):
                                first = index.sibling(index.row() + 1, 0)
                                last = last_selected
                                if last.row() != first.row():
                                    clear_selection = QtCore.QItemSelection(first, last)
                                    list_view.select(
                                        clear_selection,
                                        QtCore.QItemSelectionModel.Deselect,
                                        None,
                                    )
                                else:
                                    list_view.select(
                                        first, QtCore.QItemSelectionModel.Deselect, None
                                    )

                            # Extending selection above.
                            elif index.row() < first_selected.row():
                                first = index
                                last = first_selected.sibling(
                                    first_selected.row() - 1, 0
                                )
                                if last.isValid() and first.row() != last.row():
                                    selection = QtCore.QItemSelection(first, last)
                                    list_view.select(
                                        selection,
                                        QtCore.QItemSelectionModel.Select,
                                        last,
                                    )
                                else:
                                    list_view.select(
                                        first, QtCore.QItemSelectionModel.Select, first
                                    )

                        elif index and index.isValid():
                            list_view.select(
                                index, QtCore.QItemSelectionModel.ClearAndSelect, index
                            )
                        else:
                            list_view.clearSelection()

                        return True
        return False


# Trick IDEs for auto-completion.
_object = QtWidgets.QAbstractItemView
globals()["_object"] = object


class OQListViewMixin(OQAbstractItemViewMixin, _object):
    """
    Mix-in class for :class:`QtWidgets.QAbstractItemView` types.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQAbstractItemViewMixin`

    .. code:: python

        >>> from Qt import QtWidgets
        >>> from objettoqt.mixins import OQListViewMixin

        >>> class MixedQListView(OQListViewMixin, QtWidgets.QListView):
        ...     pass
        ...
        >>> class MixedQTreeListView(OQListViewMixin, QtWidgets.QTreeView):
        ...     pass
        ...

    :raises TypeError: Not mixed in with a :class:`QtWidgets.QAbstractItemView` class.
    """

    def __init__(self, *args, **kwargs):
        super(OQListViewMixin, self).__init__(*args, **kwargs)

        # Set initial configuration.
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setDropIndicatorShown(False)

        # Set initial configuration (overriden).
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

        # Internal event filter.
        self.__event_filter = _OQListViewMixinEventFilter(self)
        self.installEventFilter(self.__event_filter)
        self.viewport().installEventFilter(self.__event_filter)

    def setAcceptDrops(self, accept_drop):
        """
        Set whether to accept drops.

        :param accept_drop: True to accept.
        :type accept_drop: bool
        """
        super(OQListViewMixin, self).setAcceptDrops(accept_drop)

    def setDragEnabled(self, drag_enabled):
        """
        Set whether to enable drag.

        :param drag_enabled: True to enable.
        :type drag_enabled: bool
        """
        super(OQListViewMixin, self).setDragEnabled(drag_enabled)

    def setSelectionMode(self, mode):
        """
        Set selection mode.

        Allowed selection modes are:
          - :attr:`QtWidgets.QAbstractItemView.SingleSelection`
          - :attr:`QtWidgets.QAbstractItemView.ContiguousSelection`
          - :attr:`QtWidgets.QAbstractItemView.NoSelection`

        :param mode: Supported selection mode.
        :type mode: QtWidgets.QAbstractItemView.SelectionMode

        :raises ValueError: Unsupported selection mode provided.
        """
        allowed_modes = (
            QtWidgets.QAbstractItemView.SingleSelection,
            QtWidgets.QAbstractItemView.ContiguousSelection,
            QtWidgets.QAbstractItemView.NoSelection,
        )
        if mode not in allowed_modes:
            error = "selection mode {} is not supported".format(mode)
            raise ValueError(error)
        super(OQListViewMixin, self).setSelectionMode(mode)

    def setSelectionBehavior(self, behavior):
        """
        Set selection behavior.

        Allowed selection behaviors are:
          - :attr:`QtWidgets.QAbstractItemView.SelectRows`

        :param behavior: Selection behavior.
        :type behavior: QtWidgets.QAbstractItemView.SelectionBehavior

        :raises ValueError: Unsupported selection behavior provided.
        """
        allowed_behaviors = (
            QtWidgets.QAbstractItemView.SelectRows,
        )
        if behavior not in allowed_behaviors:
            error = "selection behavior {} is not supported".format(behavior)
            raise ValueError(error)
        super(OQListViewMixin, self).setSelectionBehavior(behavior)

    def setDragDropMode(self, mode):
        """
        Set drag and drop mode.

        Allowed drag and drop modes are:
          - :attr:`QtWidgets.QAbstractItemView.NoDragDrop`
          - :attr:`QtWidgets.QAbstractItemView.DragOnly`
          - :attr:`QtWidgets.QAbstractItemView.DropOnly`
          - :attr:`QtWidgets.QAbstractItemView.DragDrop`

        :param mode: Drag and drop mode.
        :type mode: QtWidgets.QAbstractItemView.DragDropMode

        :raises ValueError: Unsupported drag and drop mode provided.
        """
        allowed_modes = (
            QtWidgets.QAbstractItemView.NoDragDrop,
            QtWidgets.QAbstractItemView.DragOnly,
            QtWidgets.QAbstractItemView.DropOnly,
            QtWidgets.QAbstractItemView.DragDrop,
        )
        if mode not in allowed_modes:
            error = "drag and drop mode {} is not supported".format(mode)
            raise ValueError(error)
        super(OQListViewMixin, self).setDragDropMode(mode)

    def setDragDropOverwriteMode(self, overwrite):
        """
        Set drag and drop overwrite mode.

        :param overwrite: Only False is allowed.
        :type overwrite: bool

        :raises ValueError: Unsupported drag and drop overwwrite mode provided.
        """
        if overwrite:
            error = "drag and drop overwrite is not supported"
            raise ValueError(error)
        super(OQListViewMixin, self).setDragDropOverwriteMode(False)

    def setDefaultDropAction(self, action):
        """
        Set default drop action.

        Allowed default drop actions are:
          - :attr:`QtCore.Qt.DropAction.IgnoreAction`
          - :attr:`QtCore.Qt.DropAction.CopyAction`
          - :attr:`QtCore.Qt.DropAction.MoveAction`
          - :attr:`QtCore.Qt.DropAction.ActionMask`

        :param action: Drop action.
        :type action: QtCore.Qt.DropAction
        """
        allowed_actions = (
            QtCore.Qt.DropAction.IgnoreAction,
            QtCore.Qt.DropAction.CopyAction,
            QtCore.Qt.DropAction.MoveAction,
            QtCore.Qt.DropAction.ActionMask,
        )
        if action not in allowed_actions:
            error = "drop action {} is not supported".format(action)
            raise ValueError(error)
        super(OQListViewMixin, self).setDefaultDropAction(action)

    def select(self, selection, mode, current=None):
        """
        Select and set current.

        :param selection: Selection.
        :type selection: QtCore.QItemSelection or QtCore.QModelIndex

        :param mode: Mode.
        :type mode: QtCore.QItemSelectionModel.SelectionFlag

        :param current: Current (None will clear current).
        :type current: QtCore.QModelIndex or None
        """
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
        """
        **slot**

        Delete currently selected.
        """
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
                obj.delete(slice(first_index, last_index + 1))

    @QtCore.Slot()
    def clearCurrent(self):
        """
        **slot**

        Clear current.
        """
        selection_model = self.selectionModel()
        if selection_model is None:
            return
        self.selectionModel().clearCurrentIndex()

    @QtCore.Slot()
    def clearSelection(self):
        """
        **slot**

        Clear selection and current.
        """
        selection_model = self.selectionModel()
        if selection_model is None:
            return
        self.selectionModel().clearSelection()
        self.selectionModel().clearCurrentIndex()

    def showCustomContextMenu(self, position):
        """
        **virtual method**

        Show custom context menu.

        :param position: Position.
        :type position: QtCore.QPoint

        :return: True if shown.
        :rtype: bool
        """
        assert self is not None
        assert position is not None
        return False


class OQListView(OQListViewMixin, QtWidgets.QListView):
    """
    Mixed :class:`QtWidgets.QListView` type.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQListViewMixin`
      - :class:`QtWidgets.QListView`
    """

    def __init__(self, *args, **kwargs):
        super(OQListView, self).__init__(*args, **kwargs)


class OQTreeListView(OQListViewMixin, QtWidgets.QTreeView):
    """
    Mixed :class:`QtWidgets.QTreeView` type (for lists with multiple columns).

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQListViewMixin`
      - :class:`QtWidgets.QTreeView`
    """

    def __init__(self, *args, **kwargs):
        super(OQTreeListView, self).__init__(*args, **kwargs)

        # Set initial configuration.
        self.setRootIsDecorated(False)

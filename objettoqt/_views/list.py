# -*- coding: utf-8 -*-
"""List view."""

from objetto.objects import MutableListObject
from Qt import QtCore, QtGui, QtWidgets

from .._mixins import OQAbstractItemViewMixin

__all__ = ["OQListViewMixin", "OQListView", "OQTreeListView"]


class _OQListViewMixinEventFilter(QtCore.QObject):
    """Internal event filter for `OQListViewMixin`."""

    def __init__(self, list_view):
        assert isinstance(list_view, OQListViewMixin)
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
                list_view.deleteEnabled()
                and event.type() == QtCore.QEvent.KeyPress
                and event.key() == QtCore.Qt.Key_Delete
                and list_view.hasFocus()
                and list_view.isEnabled()
            ):
                event.accept()
                list_view.deleteSelected()
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

        # Options.
        self.__delete_enabled = True

        # Internal event filter.
        self.__event_filter = _OQListViewMixinEventFilter(self)
        self.installEventFilter(self.__event_filter)
        self.viewport().installEventFilter(self.__event_filter)

    def deleteEnabled(self):
        """
        Get whether deletion is enabled when pressing the `Del` key.

        :return: True if enabled.
        :rtype: bool
        """
        return self.__delete_enabled

    def setDeleteEnabled(self, enabled):
        """
        Set whether deletion is enabled when pressing the `Del` key.

        :param enabled: True for enabled.
        :type enabled: bool
        """
        self.__delete_enabled = bool(enabled)

    def startDrag(self, _):
        """Start drag."""

        # Can we drag?
        model = self.model()
        if not self.dragEnabled() or model is None:
            return

        # Get selected indexes.
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return
        sorted_indexes = sorted(selected_indexes, key=lambda i: i.row())
        first_index, last_index = sorted_indexes[0], sorted_indexes[-1]
        selection = QtCore.QItemSelection(first_index, last_index)

        # Get mime data.
        mime_data = model.mimeData(selected_indexes)
        if mime_data is None:
            return

        # Get drag actions from the model.
        drag_actions = model.supportedDragActions()

        # Start drag.
        viewport = self.viewport()
        drag = QtGui.QDrag(viewport)
        drag.setMimeData(mime_data)

        # Prepare pixmap.
        pixmap = QtGui.QPixmap(viewport.visibleRegion().boundingRect().size())
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        visual_rect = self.visualRegionForSelection(selection).boundingRect()
        painter.drawPixmap(visual_rect, viewport.grab(visual_rect))
        painter.end()
        drag.setPixmap(pixmap)  # TODO: gradient fade if overflowing
        drag.setHotSpot(self.viewport().mapFromGlobal(QtGui.QCursor.pos()))

        # Prepare cursor.
        move_cursor = QtGui.QCursor(QtCore.Qt.DragMoveCursor)
        copy_cursor = QtGui.QCursor(QtCore.Qt.DragCopyCursor)
        drag.setDragCursor(move_cursor.pixmap(), QtCore.Qt.MoveAction)
        drag.setDragCursor(copy_cursor.pixmap(), QtCore.Qt.CopyAction)

        # Execute drag.
        drag.exec_(drag_actions)

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
        allowed_behaviors = (QtWidgets.QAbstractItemView.SelectRows,)
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
        if False and self and position:  # for PyCharm
            pass
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

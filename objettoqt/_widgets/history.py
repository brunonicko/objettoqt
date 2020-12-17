# -*- coding: utf-8 -*-
"""History widget."""

from Qt import QtCore, QtWidgets, QtGui
from objetto import PRE, POST
from objetto.changes import Update
from objetto.history import HistoryObject

from .._models import OQListModel, ListModelHeader
from .._views import OQListViewMixin, OQListView, OQTreeListView
from .._mixins import OQWidgetMixin

__all__ = ["OQHistoryWidget"]


class _OQHistoryWidgetModel(OQListModel):

    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):

        # Text color.
        changes = self.obj()
        if changes is not None:
            history = changes._parent
            if history is not None:
                if role == QtCore.Qt.ForegroundRole:
                    if index.row() > history.index:  # TODO: use system colors
                        return QtGui.QBrush(QtGui.QColor(128, 128, 138, 100))
                    elif history.index == index.row():
                        return QtGui.QBrush(QtGui.QColor(255, 255, 255, 255))

        return super(_OQHistoryWidgetModel, self).data(index, role)


class _OQHistoryWidgetViewMixin(OQListViewMixin):

    def __init__(self, *args, **kwargs):
        super(_OQHistoryWidgetViewMixin, self).__init__(*args, **kwargs)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setAcceptDrops(False)
        self.setDragEnabled(False)
        self.activated.connect(self.__onActivated)

    @QtCore.Slot(QtCore.QModelIndex)
    def __onActivated(self, index):
        model = self.model()
        if model is None:
            return
        changes = model.obj()
        if changes is not None:
            history = changes._parent
            if history is not None and index.isValid():
                with history.app.write_context():
                    app = QtWidgets.QApplication.instance()
                    app.setOverrideCursor(QtCore.Qt.WaitCursor)
                    was_enabled = self.isEnabled()
                    self.setEnabled(False)
                    try:
                        history.set_index(index.row())
                    finally:
                        app.restoreOverrideCursor()
                        self.setEnabled(was_enabled)
                        if self.isVisible():
                            self.setFocus()

    @QtCore.Slot(QtCore.QModelIndex, QtCore.QModelIndex, object)
    def dataChanged(
        self,
        top_left=QtCore.QModelIndex(),
        bottom_right=QtCore.QModelIndex(),
        roles=(),
    ):
        model = self.model()
        if model is None:
            return
        roles = list(roles)
        try:
            super(_OQHistoryWidgetViewMixin, self).dataChanged(
                top_left, bottom_right, roles
            )
        except TypeError:
            super(_OQHistoryWidgetViewMixin, self).dataChanged(
                top_left, bottom_right
            )
        changes = model.obj()
        if changes is not None:
            history = changes._parent
            if history is not None:
                model = self.model()
                if model is not None:
                    selection_model = self.selectionModel()
                    if selection_model is not None:
                        index = model.index(history.index, 0, QtCore.QModelIndex())
                        self.activated.disconnect(self.__onActivated)
                        try:
                            selection_model.setCurrentIndex(
                                index,
                                QtCore.QItemSelectionModel.NoUpdate,
                            )
                            self.scrollTo(
                                index,
                                QtWidgets.QAbstractItemView.PositionAtCenter,
                            )
                        finally:
                            self.activated.connect(self.__onActivated)

    def setModel(self, model):
        error = "can't set model on '{}' object".format(type(self).__name__)
        raise RuntimeError(error)


class _OQHistoryWidgetListView(_OQHistoryWidgetViewMixin, OQListView):
    pass


class _OQHistoryWidgetTreeListView(_OQHistoryWidgetViewMixin, OQTreeListView):
    pass


class OQHistoryWidget(OQWidgetMixin, QtWidgets.QWidget):
    """
    Mixed :class:`QtWidgets.QWidget` type (for history objects).

    Observes actions sent from an instance of :class:`objetto.history.HistoryObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQWidgetMixin`
      - :class:`QtWidgets.QWidget`

    :param parent: Parent.
    :type parent: QtCore.QObject or None

    :param headers: Headers (or None for default).
    :type headers: tuple[objettoqt.models.AbstractListModelHeader] or None

    :param extra_headers: Extra headers.
    :type extra_headers: collections.abc.Iterable[\
objettoqt.models.AbstractListModelHeader or str] or None

    :param use_tree_list_view: If True, will use a tree list view instead of a list.
    :type use_tree_list_view: bool or None
    """

    OBase = HistoryObject
    """
    **read-only class attribute**

    Minimum `objetto` object base requirement.

    :type: type[objetto.history.HistoryObject]
    """

    def __init__(
        self,
        parent=None,
        headers=None,
        extra_headers=None,
        use_tree_list_view=None,
        *args,
        **kwargs
    ):
        super(OQHistoryWidget, self).__init__(parent=parent, *args, **kwargs)

        # Title.
        self.setWindowTitle("History")

        # Layout.
        self.__layout = QtWidgets.QVBoxLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)

        # Headers.
        if headers is None:
            headers = (ListModelHeader(title="name", fallback="---"),)
        if extra_headers is None:
            extra_headers = ()
        all_headers = tuple(headers) + tuple(extra_headers)

        # Model and view.
        if use_tree_list_view is None:
            use_tree_list_view = len(all_headers) > 1
        self.__use_tree_list_view = bool(use_tree_list_view)
        self.__view = (
            _OQHistoryWidgetTreeListView if use_tree_list_view
            else _OQHistoryWidgetListView
        )(parent=self)
        self.__model = _OQHistoryWidgetModel(parent=self.__view, headers=all_headers)
        super(_OQHistoryWidgetViewMixin, self.__view).setModel(self.__model)
        self.__layout.addWidget(self.__view)

    def __onObjChanged__(self, obj, old_obj, phase):
        super(OQHistoryWidget, self).__onObjChanged__(obj, old_obj, phase)

        if phase is PRE:
            self.__model.setObj(None)
        elif phase is POST and obj is not None:
            self.__model.setObj(obj.changes)

    def __onActionReceived__(self, action, phase):
        history = self.obj()
        if history is not None:
            if action.sender is history and phase is POST:
                change = action.change
                if isinstance(change, Update) and "index" in change.new_values:
                    old_index = change.old_values["index"]
                    new_index = change.new_values["index"]
                    first_index = min((old_index, new_index))
                    last_index = len(history.changes) - 1
                    self.__model.dataChanged.emit(
                        self.__model.index(first_index, 0, QtCore.QModelIndex()),
                        self.__model.index(last_index, 0, QtCore.QModelIndex())
                    )

    def headers(self):
        return self.__model.headers()

    def useTreeListView(self):
        return self.__use_tree_list_view

    def listView(self):
        return self.__view

    def listModel(self):
        return self.__model

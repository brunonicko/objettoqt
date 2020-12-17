# -*- coding: utf-8 -*-
"""History widget."""

from objetto import POST, PRE, data_attribute
from objetto.changes import Update
from objetto.history import HistoryObject
from Qt import QtCore, QtGui, QtWidgets
from six import string_types

from .._models import ListModelHeader, OQListModel
from .._views import OQTreeListView

__all__ = ["OQHistoryWidgetDefaultHeader", "OQHistoryWidget"]


class OQHistoryWidgetDefaultHeader(ListModelHeader):
    """
    Default header for :class:`objettoqt.widgets.OQHistoryWidget`.

    Inherits from:
      - :class:`objettoqt.models.ListModelHeader`
    """

    title = data_attribute(string_types, subtypes=True, default="name")
    """
    Title.

    :type: str
    """

    fallback = data_attribute(string_types, subtypes=True, default="---")
    """
    Fallback value.

    :type: str
    """

    def data(self, obj, row, role=QtCore.Qt.DisplayRole):
        """
        Dim/brighten text depending on the history's index.

        :param obj: History changes list.
        :type obj: objetto.objects.ListObject

        :param row: Row.
        :type row: int

        :param role: Role.
        :type role: QtCore.Qt.ItemDataRole

        :return: Data.
        :rtype: str or objetto.bases.BaseObject
        """

        # Dim/brighten text.
        history = obj._parent
        if isinstance(history, HistoryObject):
            if role == QtCore.Qt.ForegroundRole:
                if row > history.index:  # TODO: use system colors
                    return QtGui.QBrush(QtGui.QColor(128, 128, 138, 100))
                elif history.index == row:
                    return QtGui.QBrush(QtGui.QColor(255, 255, 255, 255))

        return super(OQHistoryWidgetDefaultHeader, self).data(obj, row, role=role)


class _OQHistoryWidgetModel(OQListModel):
    def setObj(self, obj):
        error = "can't call 'setObj' on internal model, use the widget's method instead"
        raise RuntimeError(error)


class OQHistoryWidget(OQTreeListView):
    """
    Mixed :class:`QtWidgets.QTreeView` type (for history objects).

    Observes actions sent from an instance of :class:`objetto.history.HistoryObject`.

    Inherits from:
      - :class:`objettoqt.views.OQTreeListView`

    :param parent: Parent.
    :type parent: QtCore.QObject or None

    :param headers: Headers (or None to use \
:class:`objettoqt.widgets.OQHistoryWidgetDefaultHeader`).
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

    def __init__(self, parent=None, headers=None, mime_type=None, *args, **kwargs):
        super(OQHistoryWidget, self).__init__(parent=parent, *args, **kwargs)

        # Default headers.
        if headers is None:
            headers = (OQHistoryWidgetDefaultHeader(),)

        # Defaults.
        self.setWindowTitle("History")
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setAcceptDrops(False)
        self.setDragEnabled(mime_type is not None)
        self.setHeaderHidden(len(headers) <= 1)

        # Model.
        self.__model = _OQHistoryWidgetModel(
            parent=self, headers=headers, mime_type=mime_type
        )
        super(OQHistoryWidget, self).setModel(self.__model)

        # Signals.
        self.activated.connect(self.__onActivated)

    def __onObjChanged__(self, obj, old_obj, phase):
        super(OQHistoryWidget, self).__onObjChanged__(obj, old_obj, phase)

        if phase is PRE:
            super(_OQHistoryWidgetModel, self.__model).setObj(None)
        elif phase is POST and obj is not None:
            super(_OQHistoryWidgetModel, self.__model).setObj(obj.changes)

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
                        self.__model.index(last_index, 0, QtCore.QModelIndex()),
                    )

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

    def setModel(self, model):
        """
        Prevent setting model.

        :param model: Model.
        :type model: QtCore.QAbstractItemModel

        :raises RuntimeError: Always raised.
        """
        error = "can't set model on '{}' object".format(type(self).__name__)
        raise RuntimeError(error)

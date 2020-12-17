# -*- coding: utf-8 -*-
"""Qt list widgets."""

from weakref import WeakKeyDictionary, WeakValueDictionary

from objetto import POST, PRE
from objetto.changes import ListInsert, ListMove
from objetto.objects import ListObject
from objetto.utils.reraise_context import ReraiseContext
from objetto.utils.type_checking import assert_is_subclass
from Qt import QtCore, QtWidgets
from six.moves import xrange as x_range

from .._mixins import OQWidgetMixin
from .._models.list import ListModelHeader, OQListModel
from .._views.list import OQListView

__all__ = ["OQWidgetListDefaultHeader", "OQWidgetList"]


_MAXIMUM_SIZE = (1 << 24) - 1


class OQWidgetListDefaultHeader(ListModelHeader):
    """
    Default header for :class:`objettoqt.widgets.OQWidgetList`.

    Inherits from:
      - :class:`objettoqt.models.ListModelHeader`
    """

    def data(self, obj, row, role=QtCore.Qt.DisplayRole):
        """
        Returns `None` for the :attr:`QtCore.Qt.DisplayRole`.

        :param obj: List object.
        :type obj: objetto.objects.ListObject

        :param row: Row.
        :type row: int

        :param role: Role.
        :type role: QtCore.Qt.ItemDataRole

        :return: Data.
        :rtype: str or objetto.bases.BaseObject
        """
        if role == QtCore.Qt.DisplayRole:
            return
        return super(OQWidgetListDefaultHeader, self).data(obj, row, role=role)


class _OQWidgetListModel(OQListModel):
    def setObj(self, obj):
        error = "can't call 'setObj' on internal model, use the widget's method instead"
        raise RuntimeError(error)


class OQWidgetList(OQListView):
    """
    List of widgets.

    Observes actions sent from an instance of :class:`objetto.bases.ListObject`.

    Inherits from:
      - :class:`objettoqt.views.OQListView`

    :param parent: Parent.
    :type parent: QtCore.QObject or None

    :param editor_widget_type: Editor widget class for items.
    :type editor_widget_type: type[objettoqt.mixins.OQWidgetMixin]

    :param header: Header (or None to use \
:class:`objettoqt.widgets.OQWidgetListDefaultHeader`).
    :type header: objettoqt.models.AbstractListModelHeader or None

    :param mime_type: Mime type.
    :type mime_type: str or None

    :param scrollable: Whether should be scrollable or change size according to editors.
    :type scrollable: bool
    """

    OBase = ListObject
    """
    **read-only class attribute**

    Minimum `objetto` object base requirement.

    :type: type[objetto.objects.ListObject]
    """

    def __init__(
        self,
        parent=None,
        editor_widget_type=None,
        header=None,
        mime_type=None,
        *args,
        **kwargs,
    ):
        super(OQWidgetList, self).__init__(parent=parent, *args, **kwargs)

        # Check required editor widget type.
        with ReraiseContext(TypeError, "didn't provide 'editor_widget_type' parameter"):
            assert_is_subclass(editor_widget_type, OQWidgetMixin)

        # Default header.
        if header is None:
            headers = (OQWidgetListDefaultHeader(),)
        else:
            headers = (header,)

        # Internal attributes.
        self.__editor_widget_type = editor_widget_type
        self.__delegate = _WidgetListDelegate(parent=self)
        self.__model = _OQWidgetListModel(
            parent=self, headers=headers, mime_type=mime_type
        )
        self.__fit_to_contents = False
        self.__minimum_fit_size = 0
        self.__maximum_fit_size = _MAXIMUM_SIZE

        # Set item delegate and internal model.
        super(OQWidgetList, self).setItemDelegate(self.__delegate)
        super(OQWidgetList, self).setModel(self.__model)

    def __updateLayout__(self):

        # Fit to contents, need to calculate fixed size.
        if self.__fit_to_contents:

            # Prepare initial information.
            size = 3
            maximum_size = self.__maximum_fit_size
            flow = self.flow()

            # For every widget.
            for widget in self.editors() or ():

                # Add widget's size depending on the flow.
                widget_size_hint = widget.sizeHint()
                if flow == QtWidgets.QListView.LeftToRight:
                    size += widget_size_hint.width()
                else:
                    size += widget_size_hint.height()

                # Exceeded maximum fit size, clamp and stop adding.
                if maximum_size is not None and size > maximum_size:
                    size = maximum_size
                    if flow == QtWidgets.QListView.LeftToRight:
                        super(OQWidgetList, self).setHorizontalScrollBarPolicy(
                            QtCore.Qt.ScrollBarAsNeeded
                        )
                    else:
                        super(OQWidgetList, self).setVerticalScrollBarPolicy(
                            QtCore.Qt.ScrollBarAsNeeded
                        )
                    break

            # Did not exceed maximum fit size.
            else:
                if flow == QtWidgets.QListView.LeftToRight:
                    super(OQWidgetList, self).setHorizontalScrollBarPolicy(
                        QtCore.Qt.ScrollBarAlwaysOff
                    )
                else:
                    super(OQWidgetList, self).setVerticalScrollBarPolicy(
                        QtCore.Qt.ScrollBarAlwaysOff
                    )
                minimum_size = self.__minimum_fit_size
                if size < minimum_size:
                    size = minimum_size

            # Set fixed dimension based on the flow.
            if flow == QtWidgets.QListView.LeftToRight:
                super(OQWidgetList, self).setFixedWidth(size)
            else:
                super(OQWidgetList, self).setFixedHeight(size)

        # Emit layout changed signal.
        self.__model.layoutChanged.emit()

    @QtCore.Slot()
    def __fixScrolling(self):

        # Custom maximum fit size hasn't been set.
        if self.__maximum_fit_size != _MAXIMUM_SIZE:
            return

        horizontal_bar = self.horizontalScrollBar()
        vertical_bar = self.verticalScrollBar()
        horizontal_bar.valueChanged.disconnect(self.__fixScrolling)
        vertical_bar.valueChanged.disconnect(self.__fixScrolling)
        flow = self.flow()
        try:
            if flow == QtWidgets.QListView.LeftToRight:
                horizontal_bar.setValue(horizontal_bar.minimum())
            else:
                vertical_bar.setValue(vertical_bar.minimum())
        finally:
            horizontal_bar.valueChanged.connect(self.__fixScrolling)
            vertical_bar.valueChanged.connect(self.__fixScrolling)

    def __onObjChanged__(self, obj, old_obj, phase):
        super(OQWidgetList, self).__onObjChanged__(obj, old_obj, phase)

        if phase is PRE:
            super(_OQWidgetListModel, self.__model).setObj(None)
        elif phase is POST and obj is not None:
            super(_OQWidgetListModel, self.__model).setObj(obj)
            for i, value in enumerate(obj):
                self.openPersistentEditor(self.__model.index(i))

    def __onActionReceived__(self, action, phase):
        super(OQWidgetList, self).__onActionReceived__(action, phase)

        if action.sender is self.__model.obj() and phase is POST:

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
                            indexes[-1],
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

            # Update layout.
            self.__updateLayout__()

    def setItemDelegate(self, value):
        """
        Prevent setting item delegate.

        :param value: Item delegate.
        :type value: QtWidgets.QItemDelegate

        :raises RuntimeError: Always raised.
        """
        error = "can't set item delegate on '{}' object".format(type(self).__name__)
        raise RuntimeError(error)

    def setModel(self, model):
        """
        Prevent setting model.

        :param model: Model.
        :type model: QtCore.QAbstractItemModel

        :raises RuntimeError: Always raised.
        """
        error = "can't set model on '{}' object".format(type(self).__name__)
        raise RuntimeError(error)

    def setMinimumHeight(self, minimum_height):
        """
        Set minimum height.

        :param minimum_height: Minimum height.
        :type minimum_height: int
        """
        if self.__fit_to_contents and self.flow() != QtWidgets.QListView.LeftToRight:
            error = (
                "can't set minimum height when 'fitToContents' is turned on and flow "
                "is from top to bottom"
            )
            raise RuntimeError(error)
        super(OQWidgetList, self).setMinimumHeight(minimum_height)

    def setMaximumHeight(self, maximum_height):
        """
        Set maximum height.

        :param maximum_height: Maximum height.
        :type maximum_height: int
        """
        if self.__fit_to_contents and self.flow() != QtWidgets.QListView.LeftToRight:
            error = (
                "can't set maximum height when 'fitToContents' is turned on and flow "
                "is from top to bottom"
            )
            raise RuntimeError(error)
        super(OQWidgetList, self).setMaximumHeight(maximum_height)

    def setMinimumWidth(self, minimum_width):
        """
        Set minimum width.

        :param minimum_width: Minimum width.
        :type minimum_width: int
        """
        if self.__fit_to_contents and self.flow() == QtWidgets.QListView.LeftToRight:
            error = (
                "can't set minimum width when 'fitToContents' is turned on and flow "
                "is from left to right"
            )
            raise RuntimeError(error)
        super(OQWidgetList, self).setMinimumWidth(minimum_width)

    def setMaximumWidth(self, maximum_width):
        """
        Set maximum width.

        :param maximum_width: Maximum width.
        :type maximum_width: int
        """
        if self.__fit_to_contents and self.flow() == QtWidgets.QListView.LeftToRight:
            error = (
                "can't set maximum width when 'fitToContents' is turned on and flow "
                "is from left to right"
            )
            raise RuntimeError(error)
        super(OQWidgetList, self).setMaximumWidth(maximum_width)

    def setFixedSize(self, width_or_size, height=None):
        """
        Set fixed size.

        :param width_or_size: Width or size.
        :type width_or_size: int or QtCore.QSize

        :param height: Height or None.
        :type height: int or None
        """
        if height is None:
            width, height = width_or_size.width(), width_or_size.height()
        else:
            width, height = int(width_or_size), int(height)

        self.setMinimumWidth(width)
        self.setMaximumWidth(width)

        self.setMinimumHeight(height)
        self.setMaximumHeight(height)

    def setHorizontalScrollBarPolicy(self, policy):
        """
        Set horizontal scrollbar policy.

        :param policy: Policy.
        :type policy: QtCore.Qt.ScrollBarPolicy
        """
        if self.__fit_to_contents and self.flow() == QtWidgets.QListView.LeftToRight:
            error = (
                "can't set horizontal scrollbar policy when 'fitToContents' is turned "
                "on and flow is from left to right"
            )
            raise RuntimeError(error)
        super(OQWidgetList, self).setHorizontalScrollBarPolicy(policy)

    def setVerticalScrollBarPolicy(self, policy):
        """
        Set vertical scrollbar policy.

        :param policy: Policy.
        :type policy: QtCore.Qt.ScrollBarPolicy
        """
        if self.__fit_to_contents and self.flow() != QtWidgets.QListView.LeftToRight:
            error = (
                "can't set vertical scrollbar policy when 'fitToContents' is turned "
                "on and flow is from top to bottom"
            )
            raise RuntimeError(error)
        super(OQWidgetList, self).setVerticalScrollBarPolicy(policy)

    def setFlow(self, flow):
        """
        Set flow. Changing this will reset the scrollbars' policies and any fixed sizes.

        :param flow: Flow.
        :type flow: QtWidgets.QListView.Flow
        """
        fit_to_contents = self.fitToContents()
        self.setFitToContents(False)
        super(OQWidgetList, self).setFlow(flow)
        self.setFitToContents(fit_to_contents)

    def minimumFitSize(self):
        """
        Get minimum 'fit to contents' size.

        :return: Minimum 'fit to contents' size.
        :rtype: int
        """
        return self.__minimum_fit_size

    def setMinimumFitSize(self, minimum_size):
        """
        Set minimum 'fit to contents' size.

        :param minimum_size: Minimum 'fit to contents' size.
        :type minimum_size: int
        """
        self.__minimum_fit_size = int(minimum_size)
        if self.__minimum_fit_size > self.__maximum_fit_size:
            self.__maximum_fit_size = self.__minimum_fit_size
        self.__updateLayout__()

    def maximumFitSize(self):
        """
        Get maximum 'fit to contents' size.

        :return: Maximum 'fit to contents' size.
        :rtype: int
        """
        return self.__maximum_fit_size

    def setMaximumFitSize(self, maximum_size):
        """
        Set maximum 'fit to contents' size.

        :param maximum_size: Maximum 'fit to contents' size.
        :type maximum_size: int
        """
        self.__maximum_fit_size = int(maximum_size)
        if self.__maximum_fit_size < self.__minimum_fit_size:
            self.__minimum_fit_size = self.__maximum_fit_size
        self.__updateLayout__()

    def fitToContents(self):
        """
        Get whether this list is set to fit its contents or not.

        :return: True if fits its contents.
        :rtype: bool
        """
        return self.__fit_to_contents

    def setFitToContents(self, fit_to_contents=True):
        """
        Set whether this list is set to fit its contents or not.
        Changing this will reset the scrollbars' policies and any fixed sizes.

        :param fit_to_contents: True to fit its contents.
        :type fit_to_contents: bool
        """
        was_fit_to_contents = self.__fit_to_contents
        self.__fit_to_contents = bool(fit_to_contents)

        # No change.
        if was_fit_to_contents is self.__fit_to_contents:
            return

        # Going from 'fit to contents' to arbitrary size.
        if was_fit_to_contents:
            self.horizontalScrollBar().valueChanged.disconnect(self.__fixScrolling)
            self.verticalScrollBar().valueChanged.disconnect(self.__fixScrolling)
            super(OQWidgetList, self).setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAsNeeded
            )
            super(OQWidgetList, self).setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAsNeeded
            )
            super(OQWidgetList, self).setMinimumHeight(0)
            super(OQWidgetList, self).setMaximumHeight(_MAXIMUM_SIZE)
            super(OQWidgetList, self).setMinimumWidth(0)
            super(OQWidgetList, self).setMaximumWidth(_MAXIMUM_SIZE)

        # Going from arbitrary size to 'fit to contents'.
        else:
            super(OQWidgetList, self).setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
            super(OQWidgetList, self).setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
            self.horizontalScrollBar().valueChanged.connect(self.__fixScrolling)
            self.verticalScrollBar().valueChanged.connect(self.__fixScrolling)

            if self.flow() != QtWidgets.QListView.LeftToRight:
                super(OQWidgetList, self).setMinimumWidth(0)
                super(OQWidgetList, self).setMaximumWidth(_MAXIMUM_SIZE)
                super(OQWidgetList, self).setMinimumHeight(0)
                super(OQWidgetList, self).setMaximumHeight(0)
            else:
                super(OQWidgetList, self).setMinimumWidth(0)
                super(OQWidgetList, self).setMaximumWidth(0)
                super(OQWidgetList, self).setMinimumHeight(0)
                super(OQWidgetList, self).setMaximumHeight(_MAXIMUM_SIZE)

            self.__fixScrolling()

        # Update layout.
        self.__updateLayout__()

    def editors(self):
        """
        Get editor widgets.

        :return: Editor widgets.
        :rtype: tuple[objettoqt.mixins.OQWidgetMixin]
        """
        obj = self.obj()
        if not obj:
            return ()
        editors = []
        for value in list(obj):
            widget = self.itemDelegate().getEditor(value)
            if widget is None:
                return ()
            editors.append(widget)
        return tuple(editors)

    def resizeEvent(self, event):
        """
        Update layout on resize.

        :param event: Resize event.
        :type event: QtGui.QResizeEvent
        """
        super(OQWidgetList, self).resizeEvent(event)
        self.__updateLayout__()

    def editorWidgetType(self):
        """
        Get editor widget class.

        :return: Editor widget class.
        :rtype: type[objettoqt.mixins.OQWidgetMixin]
        """
        return self.__editor_widget_type

    def mimeType(self):
        """
        Get mime type.

        :return: Mime type.
        :rtype: str or None
        """
        return self.__model.mimeType()


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
                    update_layout = False
                    if size != previous_size:
                        self.__sizes[editor] = size
                        update_layout = True
                    if size_hint != previous_size_hint:
                        self.__size_hints[editor] = size_hint
                        update_layout = True
                    if update_layout:
                        widget.__updateLayout__()
                    return size_hint
        return QtCore.QSize(0, 0)

    def getEditor(self, value):
        return self.__editors.get(id(value))

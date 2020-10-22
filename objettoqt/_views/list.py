# -*- coding: utf-8 -*-

from PySide2 import QtWidgets, QtCore

__all__ = ["OQListView", "OQTreeListView"]


class OQListView(QtWidgets.QListView):
    """List view."""

    def __init__(self, **kwargs):
        super(OQListView, self).__init__(**kwargs)
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

    def setSelectionMode(self, mode):
        allowed_modes = (
            QtWidgets.QAbstractItemView.SingleSelection,
            QtWidgets.QAbstractItemView.ContiguousSelection,
            QtWidgets.QAbstractItemView.NoSelection,
        )
        if mode not in allowed_modes:
            error = "selection mode {} is not supported".format(mode)
            raise ValueError(error)
        super(OQListView, self).setSelectionMode(mode)


class OQTreeListView(QtWidgets.QTreeView):
    """List view with support for multiple columns."""

    def __init__(self, **kwargs):
        super(OQTreeListView, self).__init__(**kwargs)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.setRootIsDecorated(False)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setDropIndicatorShown(False)

    def setSelectionMode(self, mode):
        allowed_modes = (
            QtWidgets.QAbstractItemView.SingleSelection,
            QtWidgets.QAbstractItemView.ContiguousSelection,
            QtWidgets.QAbstractItemView.NoSelection,
        )
        if mode not in allowed_modes:
            error = "selection mode {} is not supported".format(mode)
            raise ValueError(error)
        super(OQTreeListView, self).setSelectionMode(mode)

    def setRootIsDecorated(self, show):
        if show:
            error = "root cannot be decorated"
            raise ValueError(error)
        super(OQTreeListView, self).setRootIsDecorated(False)

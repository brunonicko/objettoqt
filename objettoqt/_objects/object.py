# -*- coding: utf-8 -*-

from PySide2 import QtCore

from .._mixins.mixin import OQObjectMixin

__all__ = ["OQObject"]


class OQObject(OQObjectMixin, QtCore.QObject):
    pass

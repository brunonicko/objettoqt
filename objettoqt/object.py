# -*- coding: utf-8 -*-
"""Mixed :class:`QtCore.QObject` class."""

from Qt import QtCore

from .mixin import OQObjectMixin

__all__ = ["OQObject"]


class OQObject(OQObjectMixin, QtCore.QObject):
    """
    Mixed :class:`QtCore.QObject` type.

    Inherits from:
      - :class:`objettoqt.mixin.OQObjectMixin`
      - :class:`QtCore.QObject`
    """

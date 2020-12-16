# -*- coding: utf-8 -*-
"""Mixed `Qt` object classes."""

from Qt import QtCore

from ._mixins import OQObjectMixin

__all__ = ["OQObject"]


class OQObject(OQObjectMixin, QtCore.QObject):
    """
    Mixed :class:`QtCore.QObject` type.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQObjectMixin`
      - :class:`QtCore.QObject`
    """

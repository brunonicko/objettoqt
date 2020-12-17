# -*- coding: utf-8 -*-
"""Widget."""

from Qt import QtWidgets

from .._mixins import OQWidgetMixin

__all__ = ["OQWidget"]


class OQWidget(OQWidgetMixin, QtWidgets.QWidget):
    """
    Mixed :class:`QtWidgets.QWidget` type.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQWidgetMixin`
      - :class:`QtWidgets.QWidget`
    """

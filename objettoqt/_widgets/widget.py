# -*- coding: utf-8 -*-
from PySide2 import QtWidgets

from .._mixins.mixin import OQObjectMixin

__all__ = ["OQWidget"]


class OQWidget(OQObjectMixin, QtWidgets.QWidget):
    pass

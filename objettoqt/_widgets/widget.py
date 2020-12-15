# -*- coding: utf-8 -*-
from Qt import QtWidgets

from ..mixin import OQObjectMixin

__all__ = ["OQWidget"]


class OQWidget(OQObjectMixin, QtWidgets.QWidget):
    pass

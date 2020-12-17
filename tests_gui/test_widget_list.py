# -*- coding: utf-8 -*-
import pytest
from objetto.applications import Application
from objetto.changes import Update
from objetto.constants import POST, PRE
from objetto.objects import Object, attribute, list_cls
from Qt import QtCore, QtWidgets

from objettoqt.mixins import OQWidgetMixin
from objettoqt.widgets import OQWidgetList


def test_widget_list():
    class Thing(Object):
        name = attribute(str, default="Foo")

    class ThingWidget(OQWidgetMixin, QtWidgets.QWidget):
        def __init__(self, **kwargs):
            super(ThingWidget, self).__init__(**kwargs)
            self.ui_label = QtWidgets.QLabel(parent=self)
            self.ui_layout = QtWidgets.QVBoxLayout()
            self.setLayout(self.ui_layout)

            self.ui_button_a = QtWidgets.QPushButton()
            self.ui_button_a.clicked.connect(self.contract)

            self.ui_button_b = QtWidgets.QPushButton()
            self.ui_button_b.clicked.connect(self.expand)

            self.ui_layout.addWidget(self.ui_button_a)
            self.ui_layout.addWidget(self.ui_label)
            self.ui_layout.addWidget(self.ui_button_b)

        @QtCore.Slot()
        def contract(self):
            self.ui_label.setContentsMargins(0, 0, 0, 0)

        @QtCore.Slot()
        def expand(self):
            self.ui_label.setContentsMargins(0, 100, 0, 100)

        def _onObjChanged(self, obj, old_obj, phase):
            if phase is PRE:
                self.ui_label.setText("")
            if phase is POST:
                if obj is not None:
                    self.ui_label.setText(obj.name)

        def _onActionReceived(self, action, phase):
            if action.sender is self.obj() and phase is POST:
                if isinstance(action.change, Update):
                    if "name" in action.change.new_values:
                        self.ui_label.setText(action.change.new_values["name"])

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name=str(i)) for i in range(10))
    lst = list_cls(Thing)(app, initial)

    window = QtWidgets.QMainWindow()
    widget = QtWidgets.QWidget()
    window.setCentralWidget(widget)
    layout = QtWidgets.QHBoxLayout()
    widget.setLayout(layout)

    widget_list_a = OQWidgetList(None, ThingWidget, "application/thing_yaml")
    widget_list_a.setObj(lst)

    widget_list_b = OQWidgetList(None, ThingWidget, "application/thing_yaml")
    widget_list_b.setFitToContents(True)
    widget_list_b.setMinimumFitSize(32)
    widget_list_b.setObj(lst)

    widget_list_c = OQWidgetList(None, ThingWidget, "application/thing_yaml")
    widget_list_c.setFitToContents(True)
    widget_list_c.setMinimumFitSize(32)
    widget_list_c.setMaximumFitSize(800)
    widget_list_c.setObj(lst)

    layout.addWidget(widget_list_a)
    layout.addWidget(widget_list_b)
    layout.addWidget(widget_list_c)

    window.show()

    qt_app.exec_()


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])

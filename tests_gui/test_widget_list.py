# -*- coding: utf-8 -*-
import pytest
from PySide2 import QtCore, QtWidgets
from objetto.applications import Application
from objetto.bases import BaseObject
from objetto.actions import Action, Phase
from objetto.changes import ObjectUpdate
from objetto.objects import Object, attribute, list_obj_cls

from objettoqt.widgets import OQWidgetList
from objettoqt.mixins import OQObjectMixin


def test_widget_list():

    class Thing(Object):
        name = attribute(str, default="Foo")

    class ThingWidget(OQObjectMixin, QtWidgets.QWidget):

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
            self.ui_label.setMargin(0)

        @QtCore.Slot()
        def expand(self):
            self.ui_label.setMargin(100)

        def _onObjChanged(self, obj, old_obj, phase):
            if phase is Phase.PRE:
                self.ui_label.setText("")
            if phase is Phase.POST:
                if obj is not None:
                    self.ui_label.setText(obj.name)

        def _onActionReceived(self, action, phase):
            if action.sender is self.obj() and phase is Phase.POST:
                if isinstance(action.change, ObjectUpdate):
                    if "name" in action.change.new_values:
                        self.ui_label.setText(action.change.new_values["name"])

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name=str(i)) for i in range(10))
    lst = list_obj_cls(Thing)(app, initial)

    window = QtWidgets.QMainWindow()
    widget = QtWidgets.QWidget()
    window.setCentralWidget(widget)
    layout = QtWidgets.QHBoxLayout()
    widget.setLayout(layout)

    widget_list_a = OQWidgetList(ThingWidget, "application/thing_yaml")
    widget_list_a.setObj(lst)

    widget_list_b = OQWidgetList(
        ThingWidget, "application/thing_yaml", scrollable=False
    )
    widget_list_b.setMinimumHeight(32)
    widget_list_b.setMaximumHeight(800)
    widget_list_b.setObj(lst)

    layout.addWidget(widget_list_a)
    layout.addWidget(widget_list_b)

    window.show()

    qt_app.exec_()


if __name__ == "__main__":
    pytest.main()

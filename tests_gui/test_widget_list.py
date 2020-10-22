# -*- coding: utf-8 -*-
import pytest
from PySide2 import QtCore, QtWidgets
from objetto.applications import Application
from objetto.bases import BaseObject
from objetto.actions import Action, Phase
from objetto.changes import ObjectUpdate
from objetto.objects import Object, attribute, list_object_cls

from objettoqt.widgets import OQWidgetList
from objettoqt.mixins import OQObjectMixin


def test_widget_list():

    class Thing(Object):
        name = attribute(str, default="Foo")

    class ThingWidget(OQObjectMixin, QtWidgets.QLabel):

        def __init__(self, **kwargs):
            super(ThingWidget, self).__init__(**kwargs)
            self.setMargin(20)

        def _onObjChanged(self, obj, old_obj, phase):
            if phase is Phase.PRE:
                self.setText("")
            if phase is Phase.POST:
                if obj is not None:
                    self.setText(obj.name)

        def _onActionReceived(self, action, phase):
            if action.sender is self.obj() and phase is Phase.POST:
                if isinstance(action.change, ObjectUpdate):
                    if "name" in action.change.new_values:
                        self.setText(action.change.new_values["name"])

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name=str(i)) for i in range(3))
    lst = list_object_cls(Thing)(app, initial)

    widget_list = OQWidgetList(ThingWidget, "application/thing_yaml")
    widget_list.setObj(lst)

    widget_list.show()
    qt_app.exec_()


if __name__ == "__main__":
    pytest.main()

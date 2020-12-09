# -*- coding: utf-8 -*-
import pytest
from PySide2 import QtWidgets
from objetto.applications import Application
from objetto.objects import Object, attribute, list_cls

from objettoqt.models import OQListModel, ListModelHeader
from objettoqt.views import OQListView


def test_list_view():

    class Thing(Object):
        name = attribute(str, default="Foo")

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name=str(i)) for i in range(1000))
    lst = list_cls(Thing)(app, initial)

    model = OQListModel(
        headers=(ListModelHeader(title="name"), ),
        mime_type="application/thing_yaml"
    )
    model.setObj(lst)

    view = OQListView()
    view.setModel(model)

    view.show()
    qt_app.exec_()


if __name__ == "__main__":
    pytest.main()

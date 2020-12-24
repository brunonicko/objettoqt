# -*- coding: utf-8 -*-
import pytest
from objetto.applications import Application
from objetto.objects import Object, attribute, list_cls
from Qt import QtWidgets

from objettoqt._models import ListModelHeader, OQListModel
from objettoqt.views import OQListView


def test_list_view():
    class Thing(Object):
        name = attribute(str, default="Foo")

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name=str(i)) for i in range(1000))
    lst_a = list_cls(Thing)(app, initial)
    lst_b = list_cls(Thing)(app)

    model_a = OQListModel(
        headers=(ListModelHeader(title="name"),), mime_type="application/thing_yaml"
    )
    model_a.setObj(lst_a)

    model_b = OQListModel(
        headers=(ListModelHeader(title="name"),), mime_type="application/thing_yaml"
    )
    model_b.setObj(lst_b)

    view_a = OQListView()
    view_a.setModel(model_a)

    view_b = OQListView()
    view_b.setModel(model_b)

    widget = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout()
    widget.setLayout(layout)
    layout.addWidget(view_a)
    layout.addWidget(view_b)

    widget.show()
    qt_app.exec_()


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])

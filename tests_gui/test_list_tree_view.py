# -*- coding: utf-8 -*-
import pytest
from Qt import QtWidgets
from objetto.applications import Application
from objetto.objects import Object, attribute, list_cls

from objettoqt.models import OQListModel, ListModelHeader
from objettoqt.views import OQTreeListView


def test_list_tree_view():

    class Thing(Object):
        name = attribute(str, default="Foo")

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name=str(i)) for i in range(3))
    lst = list_cls(Thing)(app, initial)

    model = OQListModel(
        headers=(ListModelHeader(title="name"), ),
        mime_type="application/thing_yaml"
    )
    model.setObj(lst)

    view = OQTreeListView()
    view.setModel(model)

    view.show()
    qt_app.exec_()


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])

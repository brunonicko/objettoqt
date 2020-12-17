# -*- coding: utf-8 -*-
import pytest
from objetto.applications import Application
from objetto.objects import Object, attribute, list_cls
from Qt import QtWidgets
from six import integer_types, string_types

from objettoqt._models import ListModelHeader, OQListModel
from objettoqt.views import OQTreeListView


def test_list_tree_view():
    class Thing(Object):
        name = attribute(string_types, default="Foo")
        points = attribute(integer_types, default=1)

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name=str(i), points=i + 3) for i in range(15))
    lst = list_cls(Thing)(app, initial)

    model = OQListModel(
        headers=(
            ListModelHeader(title="name"),
            ListModelHeader(title="points"),
        ),
        mime_type="application/thing_yaml",
    )
    model.setObj(lst)

    view = OQTreeListView()
    view.setModel(model)

    view.show()
    qt_app.exec_()


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])

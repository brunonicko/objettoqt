# -*- coding: utf-8 -*-
import pytest
from objetto.applications import Application
from objetto.objects import Object, attribute, list_cls
from objetto.constants import STRING_TYPES, INTEGER_TYPES
from Qt import QtWidgets

from objettoqt._models import ListModelHeader, OQListModel
from objettoqt.views import OQTreeListView


def test_list_tree_view():
    class Thing(Object):
        name = attribute(STRING_TYPES, default="Foo")
        points = attribute(INTEGER_TYPES, default=1)

    qt_app = QtWidgets.QApplication([])
    app = Application()
    initial = (Thing(app, name="Name " + str(i), points=i + 3) for i in range(15))
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

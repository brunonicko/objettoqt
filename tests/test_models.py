# -*- coding: utf-8 -*-
import pytest
from objetto.applications import Application
from objetto.objects import list_cls
from Qt import QtCore

from objettoqt._models import OQListModel


def test_list_model():
    app = Application()
    lst = list_cls(int)(app, range(10))

    model = OQListModel()
    model.setObj(lst)

    assert model.rowCount() == len(lst) == 10
    for i, v in enumerate(lst):
        assert model.data(model.index(i), role=QtCore.Qt.UserRole) == v

    lst.extend(range(21, 11, -1))
    assert model.rowCount() == len(lst) == 20

    for i, v in enumerate(lst):
        assert model.data(model.index(i), role=QtCore.Qt.UserRole) == v


if __name__ == "__main__":
    pytest.main([__file__])

# -*- coding: utf-8 -*-
import pytest
from objetto.applications import Application
from objetto.constants import POST
from objetto.objects import Object, attribute
from Qt import QtCore

from objettoqt.mixins import OQObjectMixin


def test_mixin():
    class Thing(Object):
        name = attribute(str, default="Foo")

    class DummyQObject(OQObjectMixin, QtCore.QObject):
        received = None
        changed = None

        def _onObjChanged(self, obj, old_obj, phase):
            self.changed = obj, old_obj, phase

        def _onActionReceived(self, action, phase):
            self.received = action, phase

    app = Application()
    thing = Thing(app)

    dummy = DummyQObject()
    assert dummy.objToken() is None
    dummy.setObj(thing)
    assert dummy.objToken() is not None

    assert dummy.changed is not None
    assert dummy.received is None
    thing.name = "Bar"
    assert dummy.received is not None
    assert dummy.received[-1] is POST

    dummy.setObj(None)
    assert dummy.changed == (None, thing, POST)
    assert dummy.objToken() is None
    dummy.received = None
    thing.name = "Foo"
    assert dummy.received is None
    assert dummy.changed is not None
    assert dummy.changed == (None, thing, POST)


if __name__ == "__main__":
    pytest.main([__file__])

# -*- coding: utf-8 -*-
import pytest
from objetto.applications import Application
from objetto.objects import Object, attribute
from objetto.actions import Phase

from objettoqt.mixins import OQObjectMixin


def test_mixin():
    class Thing(Object):
        name = attribute(str, default="Foo")

    class DummyQObject(OQObjectMixin):
        received = None
        changed = None

        def _onObjChanged(self, obj, old_obj, phase):
            self.changed = obj, old_obj, phase

        def _onActionReceived(self, action, phase):
            self.received = action, phase

    app = Application()
    obj = Thing(app)

    dummy = DummyQObject()
    assert dummy.objToken() is None
    dummy.setObj(obj)
    assert dummy.objToken() is not None

    assert dummy.changed is not None
    assert dummy.received is None
    obj.name = "Bar"
    assert dummy.received is not None
    assert dummy.received[-1] is Phase.POST

    dummy.setObj(None)
    assert dummy.changed == (None, obj, Phase.POST)
    assert dummy.objToken() is None
    dummy.received = None
    obj.name = "Foo"
    assert dummy.received is None
    assert dummy.changed is not None
    assert dummy.changed == (None, obj, Phase.POST)


if __name__ == "__main__":
    pytest.main()

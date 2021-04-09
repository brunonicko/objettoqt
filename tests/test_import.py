# -*- coding: utf-8 -*-
import pytest


def test_import():
    import objettoqt.models
    import objettoqt.views
    import objettoqt.widgets
    import objettoqt.mixins
    import objettoqt.objects

    assert objettoqt
    assert objettoqt.models
    assert objettoqt.views
    assert objettoqt.widgets
    assert objettoqt.mixins
    assert objettoqt.objects


if __name__ == "__main__":
    pytest.main([__file__])

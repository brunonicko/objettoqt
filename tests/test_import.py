# -*- coding: utf-8 -*-
"""Test importing from `objettoqt`."""

import pytest

__all__ = ["test_import"]


def test_import():
    import objettoqt
    assert objettoqt


if __name__ == "__main__":
    pytest.main()

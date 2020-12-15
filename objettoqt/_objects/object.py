# -*- coding: utf-8 -*-

from Qt import QtCore

from ..mixin import OQObjectMixin

__all__ = ["OQObject"]


class OQObject(OQObjectMixin, QtCore.QObject):
    """
    Mix-in class for :class:`QtCore.QObject` types.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    .. code:: python

        >>> from Qt import QtCore
        >>> from objettoqt.mixin import OQObjectMixin

        >>> class MixedQObject(OQObjectMixin, QtCore.QObject):
        ...     pass
        ...

    :raises TypeError: Not mixed in with a :class:`QtCore.QObject` class.
    """
    pass

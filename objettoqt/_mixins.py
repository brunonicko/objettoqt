# -*- coding: utf-8 -*-
"""Base mix-in class for `Qt` types."""

from inspect import getmro
from weakref import WeakKeyDictionary, ref

from objetto import POST, PRE
from objetto.bases import BaseObject
from objetto.observers import ActionObserver
from objetto.utils.reraise_context import ReraiseContext
from objetto.utils.type_checking import assert_is_instance
from Qt import QtCore, QtWidgets

__all__ = [
    "OQObjectMixin",
    "OQAbstractItemModelMixin",
    "OQWidgetMixin",
    "OQAbstractItemViewMixin",
]


class _InternalObserver(ActionObserver):
    """The actual action observer."""

    def __init__(self, qobj):
        """
        :param qobj: Objetto Qt object mixin.
        :type qobj: OQObjectMixin
        """
        self.__qobj_ref = ref(qobj)

    def __observe__(self, action, phase):
        """
        Observe an action (and its execution phase) from an object.

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: objetto.bases.Phase
        """
        qobj = self.__qobj_ref()
        if qobj is not None and not qobj.isDestroyed():
            qobj.__onActionReceived__(action, phase)
            qobj._onActionReceived(action, phase)
            qobj.actionReceived.emit(action, phase)


# Cache for mixed class checking.
_mixin_check_cache = WeakKeyDictionary()


# Trick IDEs for auto-completion.
_object = QtCore.QObject
globals()["_object"] = object


class OQObjectMixin(_object):
    """
    Mix-in class for :class:`QtCore.QObject` types.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    .. code:: python

        >>> from Qt import QtCore
        >>> from objettoqt.mixins import OQObjectMixin

        >>> class MixedQObject(OQObjectMixin, QtCore.QObject):
        ...     pass
        ...

    :raises TypeError: Not mixed in with a :class:`QtCore.QObject` class.
    """

    __observer = None
    __obj = None
    __obj_token = None
    __is_destroyed = None

    objChanged = QtCore.Signal(object, object, object)
    """
    **signal**

    Emitted when the source :class:`objetto.bases.BaseObject` changes.

    :param obj: New object (or None).
    :type obj: objetto.bases.BaseObject or None

    :param old_obj: Old object (or None).
    :type old_obj: objetto.bases.BaseObject or None

    :param phase: Phase.
    :type phase: objetto.bases.Phase
    """

    actionReceived = QtCore.Signal(object, object)
    """
    **signal**

    Emitted when an action is received.

    :param action: Action.
    :type action: objetto.objects.Action

    :param phase: Phase.
    :type phase: objetto.bases.Phase
    """

    QBase = QtCore.QObject
    """
    **read-only class attribute**

    Minimum `Qt` base requirement.

    :type: type[QtCore.QObject]
    """

    OBase = BaseObject
    """
    **read-only class attribute**

    Minimum `objetto` object base requirement.

    :type: type[objetto.bases.BaseObject]
    """

    def __init__(self, *args, **kwargs):

        # Check for expected Qt base class.
        cls = type(self)
        if cls not in _mixin_check_cache:
            visited_qbases = set()
            for base in reversed(getmro(cls)):
                if issubclass(base, OQObjectMixin):
                    qbase = base.QBase
                    if qbase in visited_qbases:
                        continue
                    visited_qbases.add(qbase)
                    if not isinstance(self, qbase):
                        error = "class '{}' is not a subclass of '{}'".format(
                            cls.__name__, qbase.__name__
                        )
                        raise TypeError(error)
            _mixin_check_cache[cls] = True

        # Initialize Qt object by passing arguments through.
        super(OQObjectMixin, self).__init__(*args, **kwargs)

        # Connect destroyed signal.
        self.destroyed.connect(self.__onDestroyed)

        # Internal attributes.
        self.__observer = _InternalObserver(self)
        self.__obj = None
        self.__obj_token = None
        self.__is_destroyed = False

    @QtCore.Slot()
    def __onDestroyed(self):
        self.__is_destroyed = True
        self._onDestroyed()

    def _onDestroyed(self):
        """
        **virtual method**

        Called *after* this has been destroyed.
        """

    def __onObjChanged__(self, obj, old_obj, phase):
        pass

    def _onObjChanged(self, obj, old_obj, phase):
        """
        **virtual method**

        Called when the source :class:`objetto.bases.BaseObject` changes.

        This method is called *before* the
        :attr:`objettoqt.mixins.OQObjectMixin.objChanged` signal gets emitted.

        :param obj: New object (or None).
        :type obj: objetto.bases.BaseObject or None

        :param old_obj: Old object (or None).
        :type old_obj: objetto.bases.BaseObject or None

        :param phase: Phase.
        :type phase: objetto.bases.Phase
        """

    def __onActionReceived__(self, action, phase):
        pass

    def _onActionReceived(self, action, phase):
        """
        **virtual method**

        Called when an action is received.

        This method is called *before* the
        :attr:`objettoqt.mixins.OQObjectMixin.actionReceived` signal gets emitted.

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: objetto.bases.Phase
        """

    def isDestroyed(self):
        """
        **final method**

        Get whether this has been destroyed or not.

        :return: True if destroyed.
        :rtype: bool
        """
        return self.__is_destroyed

    def obj(self):
        """
        **final method**

        Get the object being observed.

        :return: Object being observed (or None).
        :rtype: objetto.bases.BaseObject or None
        """
        return self.__obj

    def setObj(self, obj):
        """
        **final method**

        Set the object to observe.

        :param obj: Object to observe (or None).
        :type obj: objetto.bases.BaseObject or None
        """

        # No change.
        old_obj = self.__obj
        if obj is old_obj:
            return

        # Check 'obj' type against `OBase` from every mix-in base.
        if obj is not None:
            with ReraiseContext(TypeError, "'obj' parameter"):
                visited_obases = set()
                for base in reversed(getmro(type(self))):
                    if issubclass(base, OQObjectMixin):
                        obase = base.OBase
                        if obase in visited_obases:
                            continue
                        visited_obases.add(obase)
                        assert_is_instance(obj, (obase, None))

        # Broadcast (PRE).
        self.__onObjChanged__(obj, old_obj, PRE)
        self._onObjChanged(obj, old_obj, PRE)
        self.objChanged.emit(obj, old_obj, PRE)

        # Update internal action observer.
        if old_obj is not None:
            self.__observer.stop_observing(old_obj)
            self.__obj_token = None
        if obj is not None:
            self.__obj_token = self.__observer.start_observing(obj)
        self.__obj = obj

        # Broadcast (POST).
        self.__onObjChanged__(obj, old_obj, POST)
        self._onObjChanged(obj, old_obj, POST)
        self.objChanged.emit(obj, old_obj, POST)

    def objToken(self):
        """
        **final method**

        Get the action observer token.

        :return: Action observer token.
        :rtype: objetto.observers.ActionObserverToken
        """
        return self.__obj_token


# Trick IDEs for auto-completion.
_object = QtCore.QAbstractItemModel
globals()["_object"] = object


class OQAbstractItemModelMixin(OQObjectMixin, _object):
    """
    Mix-in class for :class:`QtCore.QAbstractItemModel` types.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQObjectMixin`

    .. code:: python

        >>> from Qt import QtCore
        >>> from objettoqt.mixins import OQAbstractItemModelMixin

        >>> class MixedQAbstractItemModel(
        ...     OQAbstractItemModelMixin, QtCore.QAbstractItemModel
        ... ):
        ...     pass
        ...

    :raises TypeError: Not mixed in with a :class:`QtCore.QAbstractItemModel` class.
    """

    QBase = QtCore.QAbstractItemModel
    """
    **read-only class attribute**

    Minimum `Qt` base requirement.

    :type: type[QtCore.QAbstractItemModel]
    """

    def __init__(self, *args, **kwargs):
        super(OQAbstractItemModelMixin, self).__init__(*args, **kwargs)


# Trick IDEs for auto-completion.
_object = QtWidgets.QWidget
globals()["_object"] = object


class OQWidgetMixin(OQObjectMixin, _object):
    """
    Mix-in class for :class:`QtWidgets.QWidget` types.

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQObjectMixin`

    .. code:: python

        >>> from Qt import QtCore
        >>> from objettoqt.mixins import OQWidgetMixin

        >>> class MixedQAbstractItemModel(OQWidgetMixin, QtWidgets.QWidget):
        ...     pass
        ...

    :raises TypeError: Not mixed in with a :class:`QtWidgets.QWidget` class.
    """

    QBase = QtWidgets.QWidget
    """
    **read-only class attribute**

    Minimum `Qt` base requirement.

    :type: type[QtWidgets.QWidget]
    """

    def __init__(self, *args, **kwargs):
        super(OQWidgetMixin, self).__init__(*args, **kwargs)


# Trick IDEs for auto-completion.
_object = QtWidgets.QAbstractItemView
globals()["_object"] = object


class OQAbstractItemViewMixin(OQWidgetMixin, _object):
    """
    Mix-in class for :class:`QtWidgets.QAbstractItemView` types (for lists).

    Observes actions sent from an instance of :class:`objetto.bases.BaseObject`.

    Inherits from:
      - :class:`objettoqt.mixins.OQWidgetMixin`

    .. code:: python

        >>> from Qt import QtWidgets
        >>> from objettoqt.mixins import OQAbstractItemViewMixin

        >>> class MixedQAbstractItemView(
        ...     OQAbstractItemViewMixin, QtWidgets.QAbstractItemView
        ... ):
        ...     pass
        ...

    :raises TypeError: Not mixed in with a :class:`QtWidgets.QAbstractItemView` class.
    """

    QBase = QtWidgets.QAbstractItemView
    """
    **read-only class attribute**

    Minimum `Qt` base requirement.

    :type: type[QtWidgets.QAbstractItemView]
    """

    def __init__(self, *args, **kwargs):
        super(OQAbstractItemViewMixin, self).__init__(*args, **kwargs)

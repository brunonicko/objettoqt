# -*- coding: utf-8 -*-
"""Mix-in class for `Qt` types."""

from weakref import ref

from Qt import QtCore

from objetto.observers import ActionObserver
from objetto import PRE, POST

__all__ = ["OQObjectMixin"]


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
            qobj._onActionReceived(action, phase)
            qobj.actionReceived.emit(action, phase)


# Trick IDEs for auto-completion.
_object = QtCore.QObject
globals()["_object"] = object


class OQObjectMixin(_object):
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

    @staticmethod
    def __OQMixinBase__():
        return OQObjectMixin

    @staticmethod
    def __OQMixedBase__():
        return QtCore.QObject

    def __OQMixedIinit__(self, *args, **kwargs):

        # Initialize Qt object by passing arguments through.
        super(OQObjectMixin, self).__init__(*args, **kwargs)

        # Check for correct mixed class.
        mixed_base = self.__OQMixedBase__()
        if isinstance(self, mixed_base):
            self.destroyed.connect(self.__onDestroyed)
        else:
            mixin_base = self.__mixin_base__()
            if type(self) is mixin_base:
                error = "can't instantiate '{}' without mixing it with a '{}'".format(
                    mixin_base.__name__, mixed_base.__name__
                )
            else:
                error = "class '{}' mixed with '{}' is not a subclass of '{}'".format(
                    type(self).__name__, mixin_base.__name__, mixed_base.__name__
                )
            raise TypeError(error)

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
        pass

    def _onObjChanged(self, obj, old_obj, phase):
        """
        **virtual method**

        Called when the source :class:`objetto.bases.BaseObject` changes.

        This method is called *before* the
        :attr:`objettoqt.mixin.OQObjectMixin.objChanged` signal gets emitted.

        :param obj: New object (or None).
        :type obj: objetto.bases.BaseObject or None

        :param old_obj: Old object (or None).
        :type old_obj: objetto.bases.BaseObject or None

        :param phase: Phase.
        :type phase: objetto.bases.Phase
        """
        pass

    @QtCore.Slot()
    def _onActionReceived(self, action, phase):
        """
        **virtual method**

        Called when an action is received.

        This method is called *before* the
        :attr:`objettoqt.mixin.OQObjectMixin.actionReceived` signal gets emitted.

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: objetto.bases.Phase
        """
        pass

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
        old_obj = self.__obj
        if obj is old_obj:
            return
        self._onObjChanged(obj, old_obj, PRE)
        self.objChanged.emit(obj, old_obj, PRE)
        if old_obj is not None:
            self.__observer.stop_observing(old_obj)
            self.__obj_token = None
        if obj is not None:
            self.__obj_token = self.__observer.start_observing(obj)
        self.__obj = obj
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
type.__setattr__(OQObjectMixin, "__init__", OQObjectMixin.__OQMixedIinit__)

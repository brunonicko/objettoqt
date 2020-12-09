# -*- coding: utf-8 -*-
"""Mix-in class for QObject types."""

from weakref import ref

from typing import TYPE_CHECKING, final
from PySide2 import QtCore

from objetto.objects import Action
from objetto.observers import ActionObserver
from objetto.bases import BaseObject, Phase

if TYPE_CHECKING:
    from typing import Optional
    from objetto.observers import ActionObserverToken

__all__ = ["OQObjectMixin"]


class _InternalObserver(ActionObserver):
    """
    The actual action observer.

    :param qobj: Objetto Qt object mixin.
    """

    def __init__(self, qobj):
        # type: (OQObjectMixin) -> None
        self.__qobj_ref = ref(qobj)

    def __observe__(self, action, phase):
        # type: (Action, Phase) -> None
        """
        Observe an action (and its execution phase) from an object.

        :param action: Action.
        :param phase: Phase.
        """
        qobj = self.__qobj_ref()
        if qobj is not None and not qobj._destroyed():
            qobj._onActionReceived(action, phase)


class OQObjectMixin(object):
    """Allows QObjects to observe actions from an objetto object."""

    def __init__(self, *args, **kwargs):
        super(OQObjectMixin, self).__init__(*args, **kwargs)
        self.__observer = _InternalObserver(self)
        self.__obj = None
        self.__obj_token = None
        self.__destroyed = False
        if isinstance(self, QtCore.QObject):
            self.destroyed.connect(self.__onDestroyed)

    @final
    def _destroyed(self):
        return self.__destroyed

    @QtCore.Slot()
    def __onDestroyed(self):
        self.__destroyed = True
        self._onDestroyed()

    def _onDestroyed(self):
        pass

    def _onObjChanged(self, obj, old_obj, phase):
        # type: (Optional[BaseObject], Optional[BaseObject], Phase) -> None
        pass

    def _onActionReceived(self, action, phase):
        # type: (Action, Phase) -> None
        pass

    def obj(self):
        # type: () -> Optional[BaseObject]
        """Get the object being observed."""
        return self.__obj

    def setObj(self, obj):
        # type: (Optional[BaseObject]) -> None
        """Set the object to observe."""
        old_obj = self.__obj
        if obj is old_obj:
            return
        self._onObjChanged(obj, old_obj, Phase.PRE)
        if old_obj is not None:
            self.__observer.stop_observing(old_obj)
            self.__obj_token = None
        if obj is not None:
            self.__obj_token = self.__observer.start_observing(obj)
        self.__obj = obj
        self._onObjChanged(obj, old_obj, Phase.POST)

    def objToken(self):
        # type: () -> Optional[ActionObserverToken]
        """Get the observer token."""
        return self.__obj_token

# -*- coding: utf-8 -*-
import pytest
from objetto import Application, Object, attribute, history_descriptor, list_attribute
from Qt import QtWidgets

from objettoqt.widgets import OQHistoryWidget


def test_history_widget():
    class Person(Object):
        name = attribute()
        age = attribute()

    class Team(Object):
        history = history_descriptor()
        people = list_attribute(Person)

    qt_app = QtWidgets.QApplication([])
    app = Application()

    team = Team(app)

    widget = OQHistoryWidget()
    widget.setObj(team.history)
    widget.setObj(None)

    person_a = Person(app, name="A", age=30)
    person_b = Person(app, name="B", age=30)
    person_c = Person(app, name="C", age=30)
    person_d = Person(app, name="D", age=30)

    team.people.extend(
        (
            person_a,
            person_b,
            person_c,
            person_d,
        )
    )

    person_a.name = "a"
    person_b.name = "b"
    person_c.name = "c"
    person_d.name = "d"

    widget.setObj(team.history)
    widget.show()
    qt_app.exec_()


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])

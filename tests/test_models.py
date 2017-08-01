""" Model tests """

import sqlalchemy
from jasper.models.remindme import RemindMeAccessor


def test_get_future_reminders(sqlite):
    accessor = RemindMeAccessor(engine=sqlite)
    assert 0 == len(accessor.get_future_reminders())

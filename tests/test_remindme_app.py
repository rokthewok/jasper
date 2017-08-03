""" Unit tests for apps.remindme """

import datetime
import pytest
from jasper.apps.remindme import RemindMe


def test_parse_message():
    expected = {
        "reminder": "Clean the house",
        "datetime": datetime.datetime(year=2017, month=8, day=1, hour=20, minute=0, second=0)
    }
    remindme = RemindMe(None, accessor="not actually an accessor")  # TODO mock this accessor properly
    result = remindme._parse_message("remindme: Clean the house on Tuesday, August 01, 2017 at 08:00:00 PM")
    assert expected == result

    result = remindme._parse_message("remindme: Clean the house on 2017-08-01T20:00:00")
    assert expected == result

    with pytest.raises(ValueError):
        result = remindme._parse_message("remindme: Clean the house on 29032191")

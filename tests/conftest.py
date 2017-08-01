""" Test configuration (for pytest) """

import pytest
import sqlalchemy
from jasper.models import Base


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture(scope="function", name="sqlite")
def make_engine():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

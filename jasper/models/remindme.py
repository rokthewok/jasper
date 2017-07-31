""" Database models for the RemindMe app """

import sqlalchemy
import sqlalchemy.orm
import datetime
from contextlib import contextmanager
from jasper.models import Base


class Reminder(Base):
    """ Represents a reminder to be posted in Discord """
    __tablename__ = "reminders"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    channel_id = sqlalchemy.Column(sqlalchemy.Text)
    user_id = sqlalchemy.Column(sqlalchemy.Text)
    reminder_date = sqlalchemy.Column(sqlalchemy.DateTime)
    creation_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())
    reminder = sqlalchemy.Column(sqlalchemy.Text)
    recurrence = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    active = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    def __repr__(self):
        return "<Reminder(id='{}', channel_id='{}', user_id='{}', " \
               "reminder_date='{}', creation_date='{}', reminder='{}', " \
               "recurrence='{}', active='{}')>".format(self.id, self.channel_id,
                                                       self.user_id, self.reminder_date,
                                                       self.creation_date, self.reminder,
                                                       self.recurrence, self.active)


class RemindMeAccess(object):
    """ Convenience query wrapper for the RemindMe app """

    def __init__(self, engine=None, **kwargs):
        self._engine = engine
        if not self._engine:
            self._engine = sqlalchemy.create_engine()
        self.SessionType = sqlalchemy.orm.sessionmaker(bind=self._engine)

    @contextmanager
    def _session(self):
        session = self.SessionType()
        yield session
        session.commit()
        session.close()

    def get_future_reminders(self):
        with self._session() as session:
            return session.query(Reminder).filter(Reminder.reminder_date > datetime.datetime.now()).all()

    def get_reminders_by_user(self, user):
        with self._session() as session:
            return session.query(Reminder).filter(Reminder.user_id == user).all()

    def delete_reminder(self, reminder_id):
        with self._session() as session:
            session.delete(Reminder).filter(Reminder.id == reminder_id)

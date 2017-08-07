""" Database models for the RemindMe app """

import sqlalchemy
import sqlalchemy.orm
import datetime
import enum
from contextlib import contextmanager
from jasper.models import Base


class RecurrenceOptions(enum.Enum):
    """ Types of recurrence for recurring reminders/events """
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Reminder(Base):
    """ Represents a reminder to be posted in Discord """
    __tablename__ = "reminders"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
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


class RemindMeAccessor(object):
    """ Convenience query wrapper for the RemindMe app """

    def __init__(self, engine=None, **kwargs):
        """ Constructor

        Args:
            engine:      Optional pre-created SQLAlchemy db engine. Engine
                         will be created if none is provided
            **dialect:   Database dialect, e.g. mysql, postgresql
            **user:      Username for db connection
            **password:  Password for given user
            **host:      Hostname for database
            **dbname:    Database name
        """
        self._engine = engine
        if not self._engine:
            self._engine = sqlalchemy.create_engine("{}://{}:{}@{}/{}".format(kwargs["dialect"],
                                                                              kwargs["user"],
                                                                              kwargs["password"],
                                                                              kwargs["host"],
                                                                              kwargs["dbname"]))
        self.SessionType = sqlalchemy.orm.sessionmaker(bind=self._engine)

    @contextmanager
    def _session(self):
        session = self.SessionType()
        yield session
        session.commit()
        session.close()

    def get_future_reminders(self):
        """ Retrieve all reminders set to occur after the current time

        Returns:
            a list of Reminder objects of reminders set to occur in the future
        """
        with self._session() as session:
            return session.query(Reminder).filter(Reminder.reminder_date > datetime.datetime.now()).all()

    def get_reminders_by_user(self, user):
        """ Retrieve all reminders for a given user ID

        Args:
            user:   Discord user ID
        Returns:
            a list of Reminder objects for the given user ID
        """
        with self._session() as session:
            return session.query(Reminder).filter(Reminder.user_id == user).all()

    def delete_reminder(self, reminder_id):
        """ Delete a reminder

        Args:
            reminder_id:   ID of the reminder to delete
        """
        with self._session() as session:
            session.delete(Reminder).filter(Reminder.id == reminder_id)

    def add_reminder(self, channel_id, user_id, reminder_date,
                     reminder, recurrence=None, active=True):
        with self._session() as session:
            Reminder(channel_id=channel_id, user_id=user_id, reminder_date=reminder_date,
                     reminder=reminder, recurrence=recurrence, active=active)
            session.add(Reminder)

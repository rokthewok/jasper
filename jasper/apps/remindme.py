""" Remind Me! App for Jasper """

import re
import enum
import datetime
from jasper.models.remindme import RemindMeAccessor
import jasper.discord.api


class DateFormats(enum.Enum):
    """ Various date formats to search for when setting a reminder datetime """
    ISO_DATETIME = "2[0-2][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]"
    EN_US = "(?P<day>(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)), " \
            "(?P<month>(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?" \
            "|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)) " \
            "(?P<date>[0-3][0-9]), (?P<year>2[0-9][0-9][0-9]) at " \
            "(?P<time>[0-1][0-9]:[0-5][0-9]:[0-5][0-9] ?(A|P)M)"


class DateParseStrings(enum.Enum):
    ISO_DATETIME = "%Y-%m-%dT%H:%M:%S"
    EN_US = "%A, %B %d, %Y at %I:%M:%S %p"


class RemindMe(object):
    """ RemindMe app functionality """
    name = "remindme"

    def __init__(self, discord, accessor=None):
        """ Constructor

        Args:
            stuff here
        """
        self._discord = discord
        self._db_accessor = accessor if accessor else RemindMeAccessor()
        self._message_regex = re.compile("remindme: (?P<reminder>.*) on (?P<datetime>({}|{}))"
                                         .format(DateFormats.EN_US.value,
                                                 DateFormats.ISO_DATETIME.value), flags=re.IGNORECASE)

    def _add_reminder(self, channel, user, reminder, reminder_date, recurrence_info=None):
        message = "Okay , @{user}, I am setting a reminder: {reminder} for {date}" \
            .format(user=user, reminder=reminder,
                    date=reminder_date.strftime(DateParseStrings.EN_US.value))

        print("adding reminder for channel: {}, user: {}, reminder: {} "
              "reminder_date: {}, recurrence_info: {}".format(channel, user, reminder,
                                                              reminder_date, recurrence_info))
        self._discord.send_message(channel, message)

    def _poll_for_events(self):
        pass

    def _get_datetime(self, date_string):
        timestamp = None
        for date_format in DateParseStrings:
            try:
                timestamp = datetime.datetime.strptime(date_string, date_format.value)
            except ValueError as e:
                pass
        return timestamp


    def _parse_message(self, message):
        """ Parse the given message content into remindme-friendly data

        Args:
            message: The message content to parse
        """
        matches = re.search(self._message_regex, message)
        if matches is not None:
            result = {
                "reminder": matches.group("reminder"),
                "datetime": self._get_datetime(matches.group("datetime"))
            }
            return result
        else:
            raise ValueError("Invalid remindme message: {}".format(message))


    def __call__(self, payload):
        try:
            result = self._parse_message(payload["content"])
            self._add_reminder(channel=payload["channel_id"], user=payload["author"]["id"],
                               reminder=result["reminder"], reminder_date=result["datetime"])
        except ValueError as e:
            print(e)
            self._discord.send_message(payload["channel_id"], "Sorry, that was an invalid reminder format.")

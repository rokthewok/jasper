""" Application entry point """

import os
import functools
import re
import sqlalchemy
import json
from jasper.discord.gateway import Gateway
from jasper.discord.gateway import GatewayEvents
from jasper.discord.api import Discord
from jasper.apps.remindme import RemindMe
from jasper.models.remindme import RemindMeAccessor


class JasperMessageHandler(object):
    """ Discord message create event handler for Jasper operations """

    def __init__(self, discord, notifier, apps):
        """ Constructor

        Args:
            discord:  A :py:class:`jasper.discord.discord.Discord` instance, used to send messages
            notifier: String notifier to indicate a message should be picked up by jasper
        """
        self._discord = discord
        self._notifier = notifier
        self._apps = { app.name : app for app in apps }

    def _get_key(self, content):
        for name in self._apps.keys():
            if re.search(name, content) is not None:
                return name
        return "help"

    def _is_jasper_message(self, content):
        return re.match(self._notifier, content) is not None

    async def __call__(self, payload):
        if self._is_jasper_message(payload["content"]):
            key = self._get_key(payload["content"])
            handler = self._apps.get(key, None)
            if handler:
               handler(payload)
            else:
                pass  # log something
        else:
            print("Not a jasper message: {}".format(payload["content"]))


def make_db_engine(config, user, password):
    return sqlalchemy.create_engine("{}://{}:{}@{}/{}".format(config["DB_DIALECT"], user, password,
                                                              config["DB_HOST"], config["DB_NAME"]))

def get_config():
    with open(os.environ["JASPER_CONFIG"], "r") as config:
        return json.load(config)


def main():
    """ Main function - all which happens, starts here """
    try:
        auth_token = os.environ["DISCORD_AUTH_TOKEN"]

        gateway = Gateway(auth_token)
        discord = Discord(auth_token)
        config = get_config()
        engine = make_db_engine(config, os.environ["JASPER_PSQL_USER"], os.environ["JASPER_PSQL_PW"])
        handler = JasperMessageHandler(discord, "!jasper",
                                       [RemindMe(discord, RemindMeAccessor(engine=engine))])
        gateway.register_handler(GatewayEvents.MESSAGE_CREATE.value, handler)
        gateway.start()
    except Exception as e:
        print(e)
        raise e

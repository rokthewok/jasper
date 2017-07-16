""" Application entry point """

import os
import functools
import jasper.discord.discord


class JasperMessageHandler(object):
    """ Discord message create event handler for Jasper operations """

    def __init__(self, discord):
        """ Constructor

        Args:
            discord:  A :py:class:`jasper.discord.discord.Discord` instance, used to send messages
        """
        self._discord = discord

    async def do_remind(self, data):
        """ Do the remind me app stuff """
        pass

    async def __call__(self, *args, **kwargs):
        pass

async def make_message_handler(discord):
    async def message_handler():
        # do message stuff here
        print("message create handler!!")
    return await message_handler()

def main():
    """ Main function - all which happens, starts here """
    try:
        auth_token = os.environ["DISCORD_AUTH_TOKEN"]
        discord = jasper.discord.discord.Discord(auth_token)
        discord.register_handler(jasper.discord.discord.DiscordEvents.MESSAGE_CREATE.value,
                                 make_message_handler(discord))
        discord.start()
    except Exception as e:
        print(e)
        raise e

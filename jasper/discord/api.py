""" ReST endpoints for Discord """

import requests
import string
from jasper.discord import _BASE_URL


class Discord(object):
    """ Main class used for interacting with Discord; meant for use with a bot user """

    def __init__(self, auth_token):
        self._auth_token = auth_token

    def send_message(self, channel_id, content, text_to_speech=False):  # TODO make async
        """ Send a message to a given channel

        Args:
            channel_id:     The id of the channel to send the message to
            content:        Text body of the message
            text_to_speech: Boolean describing whether or not this is a text-to-speech message
        Returns:
            The JSON message object returned from the Discord endpoint
        Raises:
            IOError: The request fails in some manner
        """
        message = {
            "content": content,
            "text_to_speech": text_to_speech,
        }
        headers = {
            "Authorization": "Bot {}".format(self._auth_token)
        }
        response = requests.post("{}/channels/{}/messages".format(_BASE_URL, channel_id),
                                 json=message, headers=headers)  # TODO async
        if requests.codes.ok == response.status_code:
            return response.json()  # return message object from Discord
        else:
            raise IOError(string.Template("Failed to send a message to Discord channel "
                                          "${channel}. Response code: ${code}").substitute(channel=channel_id,
                                                                                           code=response.status_code))

""" API wrapper for Discord ReST endpoints """

import requests
import websockets
import string
import threading
import time
import json
import enum


__author__ = "John Ruffer"
__email__ = "jqruffer@gmail.com"


_BASE_URL = "https://discordapp.com/api"


class Discord(object):
    """ Main class used for interacting with Discord; meant for use with a bot user """

    def __init__(self, auth_token):
        self._auth_token = auth_token

    def send_message(self, channel_id, content, text_to_speech=False):
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
                                 json=message, headers=headers)
        if requests.codes.ok == response.status_code:
            return response.json()  # return message object from Discord
        else:
            raise IOError(string.Template("Failed to send a message to Discord channel "
                                          "${channel}. Response code: ${code}").substitute(channel=channel_id,
                                                                                           code=response.status_code))


def make_payload_json(op, data, **kwargs):
    """ Make the JSON (dictionary) payload for the Gateway

    Args:
        op:      Opcode for the payload, as defined by :py:class:`GatewayOpCodes`
        data:    Data to be contained in the payload
        **seqno: Sequence number (only used by opcode 0)
        **name:  Event name (only used by opcode 0)
    Returns:
        A `dict` containing the correct key-value pairs for a Gateway payload
    """
    payload = dict()

    payload["op"] = op
    payload["d"] = data

    if kwargs.get("seqno"):
        payload["s"] = kwargs["seqno"]

    if kwargs.get("name"):
        payload["t"] = kwargs["name"]

    return payload


class GatewayOpCodes(enum.Enum):
    """ Gateway OP Codes as defined by the Discord API """
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    STATUS_UPDATE = 3
    VOICE_STATUS_UPDATE = 4
    VOICE_SERVER_FLAG = 5
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class Heartbeat(threading.Thread):
    """ Gateway heartbeat scheduler. Inherits from :py:class:`threading.Thread` """

    def __init__(self, interval, websocket):
        """ Constructor

        Args:
            interval:   Time interval for the heartbeat, in milliseconds
            websocket:  An active websocket connection
        """
        threading.Thread.__init__(self)
        self._interval = interval
        self._websocket = websocket
        self._runlock = threading.Lock()
        self._sequence_number = None
        self._sequence_number_lock = threading.Lock()
        self._running = True

    def _is_running(self):
        with self._runlock:
            return self._running

    def stop(self):
        """ Stop the currently running heartbeat """
        with self._runlock:
            if self._running:
                self._running = False

    @property
    def sequence_number(self):
        with self._sequence_number_lock:
            return self._sequence_number

    @sequence_number.setter
    def sequence_number(self, number):
        with self._sequence_number_lock:
            self._sequence_number = number

    async def run(self):
        while self._is_running():
            time.sleep(self._interval)
            await self._websocket.send(json.dumps({}))


class Gateway(object):
    """ Websockets gateway manager for Discord events """

    def __init__(self):
        pass

    def _get_gateway(self):
        """ Retrieve the gateway URL for making a websocket connection """
        response = requests.get("{}/gateway".format(_BASE_URL))
        if requests.codes.ok == response.status_code:
            data = response.json()
            self._wss_url = data["url"]
        else:
            raise IOError("unable to retrieve gateway URL")
        return self._wss_url

    async def connect(self):
        url = self._get_gateway()
        await websockets.client.connect(url)

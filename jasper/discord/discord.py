""" API wrapper for Discord ReST endpoints """

import requests
import websockets
import string
import sys
import json
import enum
import asyncio


__author__ = "John Ruffer"
__email__ = "jqruffer@gmail.com"


_BASE_URL = "https://discordapp.com/api"


class DiscordEvents(enum.Enum):
    """ Possible event types received by the gateway """
    READY = "READY"
    RESUMED = "RESUMED"
    CHANNEL_CREATE = "CHANNEL_CREATE"
    CHANNEL_UPDATE = "CHANNEL_UPDATE"
    CHANNEL_DELETE = "CHANNEL_DELETE"
    GUILD_CREATE = "GUILD_CREATE"
    GUILD_UPDATE = "GUILD_UPDATE"
    GUILD_DELETE = "GUILD_DELETE"
    GUILD_EMOJIS_UPDATE = "GUILD_EMOJIS_UPDATE"
    GUILD_INTEGRATIONS_UPDATE = "GUILD_INTEGRATIONS_UPDATE"
    GUILD_MEMBER_ADD = "GUILD_MEMBER_ADD"
    GUILD_MEMBER_REMOVE = "GUILD_MEMBER_REMOVE"
    GUILD_MEMBER_UPDATE = "GUILD_MEMBER_UPDATE"
    GUILD_MEMBERS_CHUNK = "GUILD_MEMBERS_CHUNK"
    GUILD_ROLE_CREATE = "GUILD_ROLE_CREATE"
    GUILD_ROLE_UPDATE = "GUILD_ROLE_UPDATE"
    GUILD_ROLE_DELETE = "GUILD_ROLE_DELETE"
    MESSAGE_CREATE = "MESSAGE_CREATE"
    MESSAGE_UPDATE = "MESSAGE_UPDATE"
    MESSAGE_DELETE = "MESSAGE_DELETE"
    MESSAGE_DELETE_BULK = "MESSAGE_DELETE_BULK"
    MESSAGE_REACTION_ADD = "MESSAGE_REACTION_ADD"
    MESSAGE_REACTION_REMOVE = "MESSAGE_REACTION_REMOVE"
    MESSAGE_REACTION_REMOVE_ALL = "MESSAGE_REACTION_REMOVE_ALL"
    PRESENCE_UPDATE = "PRESENCE_UPDATE"
    GAME_OBJECT = "GAME_OBJECT"
    TYPING_START = "TYPING_START"
    USER_UPDATE = "USER_UPDATE"
    VOICE_STATE_UPDATE = "VOICE_STATE_UPDATE"
    VOICE_SERVER_UPDATE = "VOICE_SERVER_UPDATE"


class Discord(object):
    """ Main class used for interacting with Discord; meant for use with a bot user """

    def __init__(self, auth_token):
        self._auth_token = auth_token
        self._gateway = Gateway(auth_token, 6)  # TODO make gateway version configurable
        self._event_handlers = dict()

    async def send_message(self, channel_id, content, text_to_speech=False):  # TODO make async
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

    def register_handler(self, event_type, async_handler):
        """ Register a handler for a given event type. Handler MUST be declared as a coroutine (async).
            Calling `register_handler` after the Discord event loop has started will result in undefined behavior

            Args:
                event_type:     The type of event to register on. There may be more than one handler registered
                                to an event type. Event type is one of :py:class:`DiscordEvents`
                async_handler:  The :py:module:`asyncio` coroutine to be registered as the handler for the given event
            Returns:
                Nothing
        """
        if not self._event_handlers.get(event_type):
            self._event_handlers[event_type] = list()
        self._event_handlers[event_type].append(async_handler)

    async def _gateway_handler(self, payload):
        """ Handler to be used for gateway messages received

        Args:
            payload:   A dictionary object parsed from the JSON payload provided by the gateway
        """
        if len(self._event_handlers.get(payload["t"], list())) > 0:
            await asyncio.wait(self._event_handlers[payload["t"]])
        else:
            print("no handler for event type: {}".format(payload["t"]))

    def start(self):
        """ Start the gate  way event loop"""
        self._gateway.start(self._gateway_handler)


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


def to_json(payload):
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


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


class Heartbeat(object):
    """ Gateway heartbeat scheduler """

    def __init__(self, interval, websocket):
        """ Constructor

        Args:
            interval:   Time interval for the heartbeat, in milliseconds
            websocket:  An active websocket connection
        """
        self._interval = interval
        self._websocket = websocket
        self._runlock = asyncio.Lock()
        self._sequence_number = None
        self._sequence_number_lock = asyncio.Lock()
        self._running = True

    async def _is_running(self):
        with await self._runlock:
            return self._running

    async def stop(self):
        """ Stop the currently running heartbeat """
        with await self._runlock:
            if self._running:
                self._running = False

    async def sequence_number(self):
        with await self._sequence_number_lock:
            return self._sequence_number

    async def set_sequence_number(self, number):
        with await self._sequence_number_lock:
            self._sequence_number = number

    async def run(self):
        while await self._is_running():
            await asyncio.sleep(self._interval)
            payload = make_payload_json(GatewayOpCodes.HEARTBEAT.value, await self.sequence_number())
            await self._websocket.send(to_json(payload))


class Gateway(object):
    """ Websockets gateway manager for Discord events """

    def __init__(self, auth_token, version):
        """ Constructor

        Args:
            auth_token:   Bot authentication token, generated by Discord
            version:      Gateway version to use
        """
        self._auth_token = auth_token
        self._version = version
        self._heartbeat = None
        self._websocket = None
        self._runlock = asyncio.Lock()
        self._running = True

    def _get_gateway(self):
        """ Retrieve the gateway URL for making a websocket connection """
        response = requests.get("{}/gateway".format(_BASE_URL))  # TODO make async
        if requests.codes.ok == response.status_code:
            data = response.json()
            self._wss_url = data["url"]
            print("gateway URL: {}".format(self._wss_url))
        else:
            raise ConnectionError("unable to retrieve gateway URL")
        return self._wss_url

    async def _identify(self):
        """ Identify this app with the Discord gateway """
        payload = {
                "token": self._auth_token,
                "properties": {
                    "$os": sys.platform,
                    "$browser": "jasper.py",
                    "$device": "jasper.py",
                    "$referrer": "",
                    "$referring_domain": ""
                },
                "compress": False,
                "large_threshold": 250
            }
        payload = make_payload_json(GatewayOpCodes.IDENTIFY.value, payload)
        print("Identify message: {}".format(to_json(payload)))
        await self._websocket.send(to_json(payload))

    async def _connect(self):
        """ Connect to the Discord gateway """
        url = self._get_gateway()
        url = "{}?v={}&encoding=json".format(url, self._version)
        self._websocket = await websockets.client.connect(url)

    def _reconnect(self):
        """ Send a reconnect message over the gateway """
        pass

    async def _is_running(self):
        with await self._runlock:
            return self._running

    async def stop(self):
        """ Stop the gateway connection loop """
        with await self._runlock:
            if self._running:
                self._running = False
                await self._heartbeat.stop()

    async def _connect_and_listen(self, gateway_handler):
        await self._connect()
        while await self._is_running():
            # here is the main state machine
            data = json.loads(await self._websocket.recv())
            if GatewayOpCodes.HELLO.value == data["op"]:
                # now, start up the heartbeat
                self._heartbeat = Heartbeat(data["d"]["heartbeat_interval"] / 1000.0, self._websocket)
                asyncio.get_event_loop().create_task(self._heartbeat.run())
                # send an Identify message
                await self._identify()
            elif GatewayOpCodes.DISPATCH.value == data["op"]:
                print("Got a dispatch message; data: {}".format(data))
                await self._heartbeat.set_sequence_number(data["s"])  # the heartbeat needs an updated sequence
                                                                  # number (only available on dispatch messages)
                await gateway_handler(data)
            elif GatewayOpCodes.RECONNECT.value == data["op"]:
                # we need to reconnect
                print("Got a reconnect message; data: {}".format(data))
                await self._reconnect()
                pass
            elif GatewayOpCodes.INVALID_SESSION.value == data["op"]:
                print("Got an invalid session message; data: {}".format(data))
                await self._websocket.close()
                raise ConnectionError("Received invalid session from the Discord gateway. Payload: {}".format(data))
            else:
                # nothing of consequence (I think...)
                print("Got some other message; data: {}".format(data))
                pass

    def start(self, gateway_handler):
        print("Connecting to gateway and starting event loop for gateway handler")
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self._connect_and_listen(gateway_handler))
        self._websocket.close()

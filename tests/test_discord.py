""" tests for the discord module """

import pytest
import requests
import asyncio
import jasper.discord.api


def mock_post(status_code, json):
    def post(*args, **kwargs):
        return type('Response', (), {"status_code": status_code, "json": lambda : json})
    return post


def test_discord(monkeypatch):
    monkeypatch.setattr(requests, "post", mock_post(requests.codes.ok, {"hello": "world"}))
    discord = jasper.discord.api.Discord('auth_token')


    async def send_message():
        data = await discord.send_message(100, "my message content")
        assert {"hello": "world"} == data

    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_message())

    with pytest.raises(IOError):
        monkeypatch.setattr(requests, "post", mock_post(requests.codes.bad_request, {"hello": "world"}))

        async def send_bad_message():
            await discord.send_message(100, "my bad message content")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_bad_message())

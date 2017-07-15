""" tests for the discord module """

import pytest
import requests
import jasper.discord.discord


def mock_post(status_code, json):
    def post(*args, **kwargs):
        return type('Response', (), {"status_code": status_code, "json": lambda : json})
    return post

def test_discord(monkeypatch):
    monkeypatch.setattr(requests, "post", mock_post(requests.codes.ok, {"hello": "world"}))
    discord = jasper.discord.discord.Discord('auth_token')
    data = discord.send_message(100, "my message content")
    assert {"hello": "world"} == data

    with pytest.raises(IOError):
        monkeypatch.setattr(requests, "post", mock_post(requests.codes.bad_request, {"hello": "world"}))
        discord.send_message(100, "my bad message content")

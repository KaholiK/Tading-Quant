from unittest import mock

import pytest

from memesensei.telegram.bot import TelegramController


class DummyMessage:
    def __init__(self):
        self.texts = []

    async def reply_text(self, text):
        self.texts.append(text)


class DummyUser:
    def __init__(self, id):
        self.id = id


class DummyUpdate:
    def __init__(self, user_id):
        self.effective_user = DummyUser(user_id)
        self.effective_message = DummyMessage()
        self.message = self.effective_message


@pytest.mark.asyncio
async def test_unauthorized_user_rejected():
    controller = TelegramController(bot_token="token", admin_ids=[1], core_base_url="http://localhost")
    update = DummyUpdate(user_id=2)
    context = mock.Mock()
    await controller.start(update, context)
    assert "Not authorized" in update.effective_message.texts[0]


@pytest.mark.asyncio
async def test_command_hits_core_api(monkeypatch):
    controller = TelegramController(bot_token="token", admin_ids=[1], core_base_url="http://localhost")
    update = DummyUpdate(user_id=1)
    context = mock.Mock()

    called = {}

    def fake_get(path):
        called["path"] = path
        return {"dry_run": True}

    monkeypatch.setattr(controller.core, "get", fake_get)
    await controller.start(update, context)
    assert called["path"] == "/status"


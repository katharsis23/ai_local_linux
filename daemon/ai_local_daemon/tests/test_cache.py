# from tests.client import client
from src.ai_local_daemon.models.message import Message
import os



def test_create_chat(cache_manager):
    chat = cache_manager.create_chat("Test Chat")

    assert chat.title == "Test Chat"
    assert chat.id_ is not None


def test_edit_chat(cache_manager):
    chat = cache_manager.create_chat("Edit Test")

    chat.add(Message(role="user", content="hello"))
    cache_manager.save_chat(chat)

    assert chat.metadata.message_count == 1


def test_reload(cache_manager):
    chat = cache_manager.create_chat("Reload Test")
    chat_id = chat.id_

    cache_manager.save_chat(chat)

    cache_manager._rebuild_index()

    reloaded = cache_manager.load_chat(chat_id)

    assert reloaded.id_ == chat_id


def test_delete_after_reload(cache_manager):
    chat = cache_manager.create_chat("Delete Test")
    chat_id = chat.id_

    cache_manager.save_chat(chat)

    # delete file manually
    os.remove(chat.path)

    cache_manager._rebuild_index()

    # should not crash
    chats = cache_manager.list_chats()

    assert all(c["id"] != chat_id for c in chats)
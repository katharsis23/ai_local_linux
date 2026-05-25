import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.ai_local_daemon.main import app
from src.ai_local_daemon.internal.approval import ApprovalManager


def test_chat_e2e_approved(tmp_path):
    test_dir = tmp_path / "foo"
    test_dir.mkdir()

    def mock_ollama_post(*args, **kwargs):
        class MockRes:
            status_code = 200
            def json(self):
                messages = kwargs.get("json", {}).get("messages", [])
                if len(messages) == 2:
                    return {"message": {"content": f'{{"action": "read_directory", "args": {{"path": "{str(test_dir)}"}}, "reason": "testing"}}'}}
                return {"message": {"content": "I have accessed the directory."}}
        return MockRes()

    with patch('httpx.AsyncClient.post', side_effect=mock_ollama_post):
        with patch.object(ApprovalManager, 'make_request', return_value=True):
            with TestClient(app) as client:
                res = client.post("/chat/prompt/", data={"prompt": f"list {str(test_dir)}"})
                assert res.status_code == 200
                assert res.json()["response"] == "I have accessed the directory."


def test_chat_e2e_rejected(tmp_path):
    test_dir = tmp_path / "bar"
    test_dir.mkdir()

    def mock_ollama_post(*args, **kwargs):
        class MockRes:
            status_code = 200
            def json(self):
                messages = kwargs.get("json", {}).get("messages", [])
                if len(messages) == 2:
                    return {"message": {"content": f'{{"action": "read_directory", "args": {{"path": "{str(test_dir)}"}}, "reason": "testing"}}'}}
                return {"message": {"content": "Access to directory denied."}}
        return MockRes()

    with patch('httpx.AsyncClient.post', side_effect=mock_ollama_post):
        with patch.object(ApprovalManager, 'make_request', return_value=False):
            with TestClient(app) as client:
                res = client.post("/chat/prompt/", data={"prompt": f"list {str(test_dir)}"})
                assert res.json()["response"] == "Access to directory denied."

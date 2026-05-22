import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from src.ai_local_daemon.main import app

@pytest.mark.asyncio
async def test_chat_e2e_approval():
    # Mock Ollama API interactions
    async def mock_ollama_post(*args, **kwargs):
        class MockRes:
            def json(self):
                messages = kwargs.get("json", {}).get("messages", [])
                
                # If this is the initial call 
                if len(messages) == 2:
                    return {
                        "message": {
                            "content": '{"action": "read_directory", "args": {"path": "/foo"}, "reason": "testing"}'
                        }
                    }
                # Final call after tool results are passed back
                return {
                    "message": {
                        "content": "I have accessed the directory."
                    }
                }
        return MockRes()

    with patch('httpx.AsyncClient.post', side_effect=mock_ollama_post):
        # Setup ASGI async client to allow concurrent requests testing
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            
            # Start the chat request asynchronously (so it doesn't block)
            chat_task = asyncio.create_task(
                client.post("/chat/prompt/", data={"prompt": "list /foo"})
            )
            
            # Poll pending requests until the tool call halts for approval
            pending_req = None
            for _ in range(10):
                await asyncio.sleep(0.1)
                res = await client.get("/request/pending")
                data = res.json()
                if data:
                    pending_req = data[0]
                    break
                    
            assert pending_req is not None
            req_id = pending_req["id"]
            
            # Approve the request to unblock the chat task
            approve_res = await client.post(f"/request/approve/{req_id}")
            assert approve_res.status_code == 200
            
            # Ensure the chat task resolves successfully
            chat_res = await chat_task
            assert chat_res.status_code == 200
            assert chat_res.json()["response"] == "I have accessed the directory."

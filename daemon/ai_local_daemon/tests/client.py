from fastapi.testclient import TestClient
from src.ai_local_daemon.main import app

client = TestClient(app=app)

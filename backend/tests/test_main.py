import os
import pytest

# Ensure environment variables are set before importing app
os.environ["TESTING"] = "true"
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://testuser:testpass@localhost:5432/codepulse_test"
if not os.environ.get("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-ci-minimum-32-chars-long"

from fastapi.testclient import TestClient
from app.main import app

def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data

def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["status"] == "online"

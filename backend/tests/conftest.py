"""Pytest configuration and fixtures"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_job_id():
    """Mock job ID for testing"""
    return "550e8400-e29b-41d4-a716-446655440000"

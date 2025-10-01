"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
import tempfile
import os
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient

from visey_recommender.api.main import app
from visey_recommender.config import settings
from visey_recommender.data.models import UserProfile, Resource
from visey_recommender.storage.feedback_store import FeedbackStore


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        temp_path = tmp.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def feedback_store(temp_db: str) -> FeedbackStore:
    """Create a FeedbackStore instance with temporary database."""
    # Temporarily override the database path
    original_path = settings.SQLITE_FEEDBACK_PATH
    settings.SQLITE_FEEDBACK_PATH = temp_db
    
    store = FeedbackStore()
    
    yield store
    
    # Restore original path
    settings.SQLITE_FEEDBACK_PATH = original_path


@pytest.fixture
def sample_user_profile() -> UserProfile:
    """Create a sample user profile for testing."""
    return UserProfile(
        user_id=123,
        industry="Technology",
        stage="Growth",
        team_size="10-50",
        funding="Series A",
        location="San Francisco"
    )


@pytest.fixture
def sample_resources() -> list[Resource]:
    """Create sample resources for testing."""
    return [
        Resource(
            id=1,
            title="How to Scale Your Startup",
            link="https://example.com/scale-startup",
            excerpt="Learn the fundamentals of scaling a technology startup",
            categories=["Business", "Growth"],
            tags=["startup", "scaling", "growth"],
            meta={"difficulty": "intermediate", "read_time": "10 min"}
        ),
        Resource(
            id=2,
            title="Fundraising Guide for Series A",
            link="https://example.com/series-a-guide",
            excerpt="Complete guide to raising Series A funding",
            categories=["Funding", "Investment"],
            tags=["fundraising", "series-a", "investment"],
            meta={"difficulty": "advanced", "read_time": "15 min"}
        ),
        Resource(
            id=3,
            title="Building Remote Teams",
            link="https://example.com/remote-teams",
            excerpt="Best practices for managing remote development teams",
            categories=["Management", "Remote Work"],
            tags=["remote", "team", "management"],
            meta={"difficulty": "beginner", "read_time": "8 min"}
        )
    ]


@pytest.fixture
def mock_wp_client():
    """Create a mock WordPress client."""
    mock = AsyncMock()
    
    # Mock user profile response
    mock.fetch_user_profile.return_value = {
        "industry": "Technology",
        "stage": "Growth",
        "team_size": "10-50",
        "funding": "Series A",
        "location": "San Francisco"
    }
    
    # Mock resources response
    mock.fetch_resources.return_value = [
        {
            "id": 1,
            "title": "How to Scale Your Startup",
            "link": "https://example.com/scale-startup",
            "excerpt": "Learn the fundamentals of scaling a technology startup",
            "categories": ["Business", "Growth"],
            "tags": ["startup", "scaling", "growth"],
            "meta": {"difficulty": "intermediate"}
        },
        {
            "id": 2,
            "title": "Fundraising Guide for Series A",
            "link": "https://example.com/series-a-guide",
            "excerpt": "Complete guide to raising Series A funding",
            "categories": ["Funding", "Investment"],
            "tags": ["fundraising", "series-a", "investment"],
            "meta": {"difficulty": "advanced"}
        }
    ]
    
    return mock


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.ping.return_value = True
    return mock


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings to default values after each test."""
    original_values = {
        'WP_BASE_URL': settings.WP_BASE_URL,
        'CACHE_BACKEND': settings.CACHE_BACKEND,
        'TOP_N': settings.TOP_N,
        'CONTENT_WEIGHT': settings.CONTENT_WEIGHT,
        'COLLAB_WEIGHT': settings.COLLAB_WEIGHT,
        'POP_WEIGHT': settings.POP_WEIGHT,
        'EMB_WEIGHT': settings.EMB_WEIGHT
    }
    
    yield
    
    # Restore original values
    for key, value in original_values.items():
        setattr(settings, key, value)


@pytest.fixture
def mock_environment(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        'WP_BASE_URL': 'https://test-wp.example.com',
        'WP_AUTH_TYPE': 'none',
        'CACHE_BACKEND': 'sqlite',
        'TOP_N': '5',
        'CONTENT_WEIGHT': '0.7',
        'COLLAB_WEIGHT': '0.2',
        'POP_WEIGHT': '0.1',
        'EMB_WEIGHT': '0.0'
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    return test_env


class AsyncContextManager:
    """Helper for testing async context managers."""
    
    def __init__(self, async_obj):
        self.async_obj = async_obj
    
    async def __aenter__(self):
        return self.async_obj
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context():
    """Helper fixture for creating async context managers in tests."""
    return AsyncContextManager
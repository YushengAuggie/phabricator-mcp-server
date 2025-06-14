"""Pytest configuration and shared fixtures."""

import asyncio
from unittest.mock import patch

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_token():
    """Mock environment with test token."""
    with patch.dict(
        'os.environ',
        {
            'PHABRICATOR_TOKEN': 'test-token-32chars-long-string',
            'PHABRICATOR_URL': 'https://test.phabricator.com/api/',
        },
    ):
        yield


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        'id': '123',
        'fields': {
            'name': 'Sample Task',
            'status': {'name': 'Open'},
            'priority': {'name': 'High'},
            'description': {'raw': 'This is a sample task description'},
            'authorPHID': 'PHID-USER-author',
            'assignedPHID': 'PHID-USER-assignee',
        },
    }


@pytest.fixture
def sample_differential_data():
    """Sample differential data for testing."""
    return {
        'id': '456',
        'fields': {
            'title': 'Sample Differential',
            'status': {'name': 'Needs Review'},
            'authorPHID': 'PHID-USER-author',
            'summary': 'This is a sample differential summary',
        },
    }


@pytest.fixture
def sample_comments():
    """Sample comments data for testing."""
    return [
        {'type': 'comment', 'comments': 'This is the first comment', 'authorPHID': 'PHID-USER-1'},
        {'type': 'comment', 'comments': 'This is the second comment', 'authorPHID': 'PHID-USER-2'},
    ]

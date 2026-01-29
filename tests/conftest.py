"""Pytest fixtures."""

import pytest


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture
def base_url() -> str:
    return "https://test.mivia.ai/api"

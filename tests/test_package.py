"""Minimal package tests."""

import pytest

import mivia
from mivia import MiviaClient, SyncMiviaClient
from mivia.exceptions import AuthenticationError


def test_version_exists() -> None:
    """Test that version is defined."""
    assert hasattr(mivia, "__version__")
    assert isinstance(mivia.__version__, str)
    assert mivia.__version__ != "0.0.0+dev"


def test_exports() -> None:
    """Test that main classes are exported."""
    assert hasattr(mivia, "MiviaClient")
    assert hasattr(mivia, "SyncMiviaClient")
    assert hasattr(mivia, "MiviaError")


def test_client_requires_api_key() -> None:
    """Test that client requires API key."""
    with pytest.raises(AuthenticationError):
        MiviaClient()


def test_sync_client_requires_api_key() -> None:
    """Test that sync client requires API key when making requests."""
    # SyncMiviaClient defers validation until method calls
    client = SyncMiviaClient()
    with pytest.raises(AuthenticationError):
        client.list_models()

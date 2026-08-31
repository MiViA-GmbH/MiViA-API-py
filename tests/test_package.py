import pytest

import mivia
from mivia import MiviaClient, SyncMiviaClient
from mivia.exceptions import AuthenticationError


def test_version_exists() -> None:
    assert hasattr(mivia, "__version__")
    assert isinstance(mivia.__version__, str)
    assert mivia.__version__ != "0.0.0+dev"


def test_exports() -> None:
    assert hasattr(mivia, "MiviaClient")
    assert hasattr(mivia, "SyncMiviaClient")
    assert hasattr(mivia, "MiviaError")


def test_client_requires_api_key() -> None:
    with pytest.raises(AuthenticationError):
        MiviaClient()


def test_sync_client_requires_api_key() -> None:
    with pytest.raises(AuthenticationError):
        SyncMiviaClient()

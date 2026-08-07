"""MiViA Python API client."""

from mivia._merge import deep_merge
from mivia.client import MiviaClient
from mivia.exceptions import (
    AuthenticationError,
    JobTimeoutError,
    MiviaError,
    NotFoundError,
    ServerError,
    ValidationError,
)
from mivia.models import (
    CreateJobsRequest,
    CreateReportRequest,
    CustomizationDto,
    ImageDto,
    JobDto,
    JobListResponse,
    JobStatus,
    JobStatusDto,
    ModelDto,
)
from mivia.sync_client import SyncMiviaClient

__all__ = [
    # Clients
    "MiviaClient",
    "SyncMiviaClient",
    # Exceptions
    "MiviaError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "JobTimeoutError",
    # Models
    "ImageDto",
    "ModelDto",
    "CustomizationDto",
    "JobDto",
    "JobStatusDto",
    "JobStatus",
    "JobListResponse",
    "CreateJobsRequest",
    "CreateReportRequest",
    # Helpers
    "deep_merge",
]

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mivia")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"

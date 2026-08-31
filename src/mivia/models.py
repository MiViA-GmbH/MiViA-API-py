from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobStatus(str, Enum):
    CACHED = "CACHED"
    NEW = "NEW"
    FAILED = "FAILED"
    PENDING = "PENDING"


class JobSource(str, Enum):
    WEB = "WEB"
    API = "API"
    SANDBOX = "SANDBOX"
    TEST = "TEST"
    IDENTIFICATION = "IDENTIFICATION"


class ModelAccessType(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class ImageDto(BaseModel):
    """Image data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    created_at: datetime = Field(alias="createdAt")
    filename: str
    thumbnail: str
    original_filename: str = Field(alias="orginalFilename")  # Note: server typo
    validated: bool
    placeholder: str | None = None
    width: int | None = None
    height: int | None = None


class ModelDto(BaseModel):
    """Model data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str
    display_name: str = Field(alias="displayName")
    access_type: ModelAccessType = Field(alias="accessType")
    is_default_visible: bool = Field(alias="isDefaultVisible")
    description_en: str | None = None
    description_de: str | None = None


class CustomizationNameDto(BaseModel):
    """Customization name in multiple languages."""

    en: str
    de: str


class CustomizationDto(BaseModel):
    """Customization data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: CustomizationNameDto

    @property
    def name_en(self) -> str:
        return self.name.en

    @property
    def name_de(self) -> str:
        return self.name.de


class JobMaskDto(BaseModel):
    """Job mask data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    parent_id: int | None = Field(None, alias="parentId")
    label: str
    filename: str
    is_submitted: bool = Field(alias="isSubmitted")


class JobFeedbackDto(BaseModel):
    """User rating attached to a job."""

    rating: int
    comment: str | None = None


class JobModelFeedbackDto(BaseModel):
    """Single model-emitted quality flag."""

    name: str
    value: bool
    score: float


class JobImageDto(BaseModel):
    """Source image summary embedded in a job."""

    model_config = ConfigDict(populate_by_name=True)

    orginal_filename: str = Field(alias="orginalFilename")  # Note: server typo
    created_at: datetime = Field(alias="createdAt")
    id: UUID | None = None  # Only in GET /v2/jobs/{id}


class JobImageUrlsDto(BaseModel):
    """Short-lived presigned URLs for the source image."""

    model_config = ConfigDict(populate_by_name=True)

    display_url: str = Field(alias="displayUrl")
    original_url: str = Field(alias="originalUrl")
    view_url: str | None = Field(None, alias="viewUrl")


class JobResultDto(BaseModel):
    """Computed result attached to a job."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID | None = None  # Only in GET /v2/jobs/{id}
    feedback: list[JobModelFeedbackDto] | None = None
    results: list[Any] | None = None  # Only in GET /v2/jobs/{id}


class JobModelDto(BaseModel):
    """Model summary embedded in a job."""

    model_config = ConfigDict(populate_by_name=True)

    display_name: str = Field(alias="displayName")


class JobCustomizationTemplateDto(BaseModel):
    """Customization template embedded in a job."""

    model_config = ConfigDict(populate_by_name=True)

    name_en: str = Field(alias="nameEn")
    name_de: str = Field(alias="nameDe")
    config: dict[str, Any] | None = None


class JobCustomizationDto(BaseModel):
    """Job customization embedded object."""

    model_config = ConfigDict(populate_by_name=True)

    config: dict[str, Any] | None = None
    template: JobCustomizationTemplateDto | None = None


class JobDto(BaseModel):
    """Job data transfer object (V2 and POST /jobs response)."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    image_id: UUID | None = Field(None, alias="imageId")
    model_id: UUID = Field(alias="modelId")
    result_id: UUID | None = Field(None, alias="resultId")
    status: JobStatus
    has_results: bool | None = Field(None, alias="hasResults")  # Only in GET /v2/jobs
    outdated: bool
    created_at: datetime = Field(alias="createdAt")
    started_at: datetime | None = Field(None, alias="startedAt")
    finished_at: datetime | None = Field(None, alias="finishedAt")
    model_version: str | None = Field(None, alias="modelVersion")
    image: JobImageDto | None = None  # Only in GET /v2/jobs
    result: JobResultDto | None = None  # Only in GET /v2/jobs
    customization_id: UUID | None = Field(None, alias="customizationId")
    masks_pending: int | None = Field(None, alias="masksPending")
    masks_submitted: int | None = Field(None, alias="masksSubmitted")
    user_feedback: JobFeedbackDto | None = Field(None, alias="userFeedback")
    with_masks: bool = Field(alias="withMasks")

    # Only in GET /v2/jobs/{id}
    source: JobSource | None = None
    model: JobModelDto | None = None
    image_urls: JobImageUrlsDto | None = Field(None, alias="imageUrls")
    masks: list[JobMaskDto] | None = None
    customization: JobCustomizationDto | None = None

    @property
    def results(self) -> list[Any] | None:
        """Computed results, present once the job is fetched with get_job()."""
        return self.result.results if self.result else None

    @property
    def image_filename(self) -> str | None:
        return self.image.orginal_filename if self.image else None

    @field_validator("customization", mode="before")
    @classmethod
    def empty_dict_to_none(cls, v: Any) -> Any:
        if isinstance(v, dict) and not v:
            return None
        return v


class JobStatusDto(BaseModel):
    """Fields that change while a job runs, from GET /v2/jobs/status."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    status: JobStatus
    result_id: UUID | None = Field(None, alias="resultId")
    finished_at: datetime | None = Field(None, alias="finishedAt")


class PaginationDto(BaseModel):
    """Pagination metadata."""

    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)


class JobListResponse(BaseModel):
    """Response for job list endpoint."""

    data: list[JobDto]
    pagination: PaginationDto


class CreateJobsRequest(BaseModel):
    """Request body for creating jobs."""

    model_config = ConfigDict(populate_by_name=True)

    image_ids: list[UUID] = Field(serialization_alias="imageIds")
    model_id: UUID = Field(serialization_alias="modelId")
    customization_id: UUID | None = Field(None, serialization_alias="customizationId")
    source: JobSource = JobSource.API
    customization_config_override: dict[str, Any] | None = Field(
        None, serialization_alias="customizationConfigOverride"
    )


class CreateReportRequest(BaseModel):
    """Request body for creating reports."""

    model_config = ConfigDict(populate_by_name=True)

    jobs_ids: list[UUID] = Field(serialization_alias="jobsIds")
    tz_offset: int | None = Field(None, serialization_alias="tzOffset")
    include_images: bool | None = Field(True, serialization_alias="includeImages")

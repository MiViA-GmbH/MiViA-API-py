import asyncio
import os
from pathlib import Path
from typing import Any, Self
from uuid import UUID

import httpx

from mivia.exceptions import (
    AuthenticationError,
    JobTimeoutError,
    MiviaError,
    NotFoundError,
    PermissionError,
    RateLimitError,
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


class MiviaClient:
    """Async HTTP client for MiViA API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        proxy: str | None = None,
    ):
        """
        Initialize MiViA client.

        Args:
            api_key: API key. If None, reads from MIVIA_API_KEY env var.
            base_url: Base URL. If None, reads from MIVIA_BASE_URL or uses default.
            timeout: Request timeout in seconds.
            proxy: Proxy URL. If None, reads from MIVIA_PROXY env var.
        """
        self._api_key = api_key or os.environ.get("MIVIA_API_KEY")
        if not self._api_key:
            raise AuthenticationError("API key required. Set MIVIA_API_KEY env var.")

        self._base_url = (
            base_url or os.environ.get("MIVIA_BASE_URL") or "https://app.mivia.ai/api"
        )
        self._timeout = timeout
        self._proxy = proxy or os.environ.get("MIVIA_PROXY")
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": self._api_key},
            timeout=self._timeout,
            proxy=self._proxy,
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise MiviaError("Client not initialized. Use 'async with' context.")
        return self._client

    @staticmethod
    def _detail(response: httpx.Response, fallback: str) -> str:
        try:
            return str(response.json().get("message", fallback))
        except Exception:
            return response.text or fallback

    def _handle_response(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise AuthenticationError()
        if response.status_code == 403:
            raise PermissionError(self._detail(response, "Not allowed"))
        if response.status_code == 404:
            raise NotFoundError()
        if response.status_code == 400:
            raise ValidationError(self._detail(response, "Validation error"))
        if response.status_code == 429:
            raise RateLimitError(
                self._detail(response, "Too many requests, retry once one finishes")
            )
        if response.status_code >= 500:
            raise ServerError(f"Server error: {response.status_code}")
        response.raise_for_status()

    async def upload_image(
        self,
        file_path: Path | str,
        forced: bool = False,
    ) -> ImageDto:
        """
        Upload single image.

        Args:
            file_path: Path to image file.
            forced: Bypass quality requirements.

        Returns:
            Uploaded image DTO.
        """
        images = await self.upload_images([file_path], [forced] if forced else None)
        return images[0]

    async def upload_images(
        self,
        file_paths: list[Path | str],
        forced: list[bool] | None = None,
        reuse_existing: bool = True,
    ) -> list[ImageDto]:
        """
        Upload multiple images.

        Args:
            file_paths: List of paths to image files.
            forced: List of forced flags per image.
            reuse_existing: If upload returns empty (duplicate), find existing image.

        Returns:
            List of uploaded image DTOs.
        """
        client = self._ensure_client()

        paths = [Path(p) for p in file_paths]
        files = [("files", (p.name, p.read_bytes())) for p in paths]

        # Server requires forced array (one per file)
        forced_flags = forced if forced else [False] * len(file_paths)
        data = {"forced": [str(f).lower() for f in forced_flags]}

        response = await client.post("/image", files=files, data=data)
        self._handle_response(response)
        uploaded = [ImageDto.model_validate(img) for img in response.json()]

        if reuse_existing and len(uploaded) < len(paths):
            uploaded_names = {img.original_filename for img in uploaded}
            missing_names = {p.name for p in paths} - uploaded_names

            if missing_names:
                existing = await self.list_images()
                for img in existing:
                    if img.original_filename in missing_names:
                        uploaded.append(img)
                        missing_names.discard(img.original_filename)

        return uploaded

    async def list_images(self) -> list[ImageDto]:
        """
        List user's uploaded images.

        Returns:
            List of image DTOs.
        """
        client = self._ensure_client()
        response = await client.get("/image")
        self._handle_response(response)
        return [ImageDto.model_validate(img) for img in response.json()]

    async def delete_image(self, image_id: UUID) -> None:
        """
        Delete an image.

        Args:
            image_id: Image UUID.
        """
        client = self._ensure_client()
        response = await client.delete(f"/image/{image_id}")
        self._handle_response(response)

    async def list_models(self) -> list[ModelDto]:
        """
        List available models.

        Returns:
            List of model DTOs.
        """
        client = self._ensure_client()
        response = await client.get("/models")
        self._handle_response(response)
        return [ModelDto.model_validate(m) for m in response.json()]

    async def get_model_customizations(self, model_id: UUID) -> list[CustomizationDto]:
        """
        Get customizations for a model.

        Args:
            model_id: Model UUID.

        Returns:
            List of customization DTOs.
        """
        client = self._ensure_client()
        response = await client.get(f"/models/{model_id}/customizations")
        self._handle_response(response)
        return [CustomizationDto.model_validate(c) for c in response.json()]

    async def get_resolved_customization_config(
        self, customization_id: UUID
    ) -> dict[str, Any]:
        """
        Get the fully resolved customization config (after parent merge).

        Admin-only on the server. The returned dict is the same JSON the
        server would use if you simply created jobs with this customization
        and no override.

        Args:
            customization_id: Customization group UUID.

        Returns:
            Resolved config JSON.
        """
        client = self._ensure_client()
        response = await client.get(
            f"/admin/customizations/groups/{customization_id}/resolved-settings"
        )
        self._handle_response(response)
        return response.json()

    async def create_jobs(
        self,
        image_ids: list[UUID],
        model_id: UUID,
        customization_id: UUID | None = None,
        customization_config_override: dict[str, Any] | None = None,
    ) -> list[JobDto]:
        """
        Create computation jobs.

        Args:
            image_ids: List of image UUIDs.
            model_id: Model UUID.
            customization_id: Optional customization UUID. Used as the baseline
                template (preserved on the resulting JobCustomization rows even
                when an override is supplied).
            customization_config_override: Admin-only. Full inline customization
                config that replaces the resolved template config for these jobs
                only. The stored customization group is not modified. Non-admin
                callers receive 403 if this is set. For partial overrides use
                ``create_jobs_with_patch``.

        Returns:
            List of created job DTOs.
        """
        client = self._ensure_client()

        request = CreateJobsRequest(
            image_ids=image_ids,
            model_id=model_id,
            customization_id=customization_id,
            customization_config_override=customization_config_override,
        )

        response = await client.post(
            "/jobs",
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        self._handle_response(response)
        return [JobDto.model_validate(j) for j in response.json()]

    async def get_job(self, job_id: UUID) -> JobDto:
        """
        Get job details (v2 with results).

        Args:
            job_id: Job UUID.

        Returns:
            Job DTO with results.
        """
        client = self._ensure_client()
        response = await client.get(f"/v2/jobs/{job_id}")
        self._handle_response(response)
        return JobDto.model_validate(response.json())

    async def get_recent_job_ids(
        self,
        since: str = "1h",
        model_id: UUID | None = None,
    ) -> list[UUID]:
        """
        Get IDs of recently created jobs.

        Args:
            since: Duration string (e.g. "1h", "30m", "2d").
            model_id: Optional filter by model.

        Returns:
            List of job UUIDs.
        """
        client = self._ensure_client()

        params: dict = {"idOnly": "true", "source": "API", "since": since}
        if model_id:
            params["modelId"] = str(model_id)

        response = await client.get("/jobs", params=params)
        self._handle_response(response)

        return [UUID(item["id"]) for item in response.json()]

    async def list_jobs(
        self,
        model_id: UUID | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> JobListResponse:
        """
        List jobs with pagination.

        Args:
            model_id: Optional filter by model.
            page: Page number (1-indexed).
            page_size: Items per page.
            sort_by: Sort field.
            sort_order: Sort order (asc/desc).

        Returns:
            Job list response with pagination.
        """
        client = self._ensure_client()

        params = {
            "page": page,
            "pageSize": page_size,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        if model_id:
            params["modelId"] = str(model_id)

        response = await client.get("/v2/jobs", params=params)
        self._handle_response(response)
        return JobListResponse.model_validate(response.json())

    async def get_jobs_status(self, job_ids: list[UUID]) -> list[JobStatusDto]:
        """
        Get the current state of specific jobs.

        Returns only the fields that change while a job runs, so a client
        tracking in-flight work does not have to refetch the whole list.
        Unknown or foreign job IDs are omitted from the response.

        Args:
            job_ids: Job UUIDs to poll, at most 100.

        Returns:
            Current state of each known job.
        """
        if not job_ids:
            return []

        client = self._ensure_client()
        response = await client.get(
            "/v2/jobs/status",
            params={"ids": ",".join(str(job_id) for job_id in job_ids)},
        )
        self._handle_response(response)
        return [JobStatusDto.model_validate(j) for j in response.json()]

    async def list_all_jobs(
        self,
        model_id: UUID | None = None,
        status: JobStatus | list[JobStatus] | None = None,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
        page_size: int = 100,
    ) -> list[JobDto]:
        """
        List all jobs with automatic pagination.

        Args:
            model_id: Optional filter by model.
            status: Optional filter by status (single or list).
            sort_by: Sort field.
            sort_order: Sort order (asc/desc).
            page_size: Items per page for pagination.

        Returns:
            List of all job DTOs matching criteria.
        """
        all_jobs: list[JobDto] = []
        page = 1

        while True:
            response = await self.list_jobs(
                model_id=model_id,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            jobs = response.data
            if status is not None:
                statuses = [status] if isinstance(status, JobStatus) else status
                jobs = [j for j in jobs if j.status in statuses]

            all_jobs.extend(jobs)

            if page >= response.pagination.total_pages:
                break
            page += 1

        return all_jobs

    async def wait_for_job(
        self,
        job_id: UUID,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> JobDto:
        """
        Poll until job completes or times out.

        Args:
            job_id: Job UUID.
            timeout: Max wait time in seconds.
            poll_interval: Time between polls in seconds.

        Returns:
            Completed job DTO.

        Raises:
            JobTimeoutError: If timeout exceeded.
        """
        elapsed = 0.0
        while elapsed < timeout:
            job = await self.get_job(job_id)
            if job.status in (JobStatus.CACHED, JobStatus.NEW, JobStatus.FAILED):
                return job
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise JobTimeoutError(f"Job {job_id} did not complete within {timeout}s")

    async def wait_for_jobs(
        self,
        job_ids: list[UUID],
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> list[JobDto]:
        """
        Wait for multiple jobs concurrently.

        Args:
            job_ids: List of job UUIDs.
            timeout: Max wait time in seconds.
            poll_interval: Time between polls in seconds.

        Returns:
            List of completed job DTOs.
        """
        tasks = [self.wait_for_job(jid, timeout, poll_interval) for jid in job_ids]
        return await asyncio.gather(*tasks)

    async def download_pdf(
        self,
        job_ids: list[UUID],
        output_path: Path | str,
        tz_offset: int | None = None,
    ) -> Path:
        """
        Queue a PDF report and wait for the worker to render it.

        Args:
            job_ids: List of job UUIDs.
            output_path: Path to save PDF.
            tz_offset: Client timezone offset in minutes.

        Returns:
            Path to saved file.
        """
        request = CreateReportRequest(
            jobs_ids=job_ids,
            tz_offset=tz_offset,
        )
        return await self._download_report("pdf", request, output_path)

    async def download_csv(
        self,
        job_ids: list[UUID],
        output_path: Path | str,
        include_images: bool = True,
    ) -> Path:
        """
        Queue a CSV report and wait for the worker to build the archive.

        Args:
            job_ids: List of job UUIDs.
            output_path: Path to save ZIP.
            include_images: Include images in ZIP.

        Returns:
            Path to saved file.
        """
        request = CreateReportRequest(
            jobs_ids=job_ids,
            include_images=include_images,
        )
        return await self._download_report("csv", request, output_path)

    async def _download_report(
        self,
        format: str,
        request: CreateReportRequest,
        output_path: Path | str,
        timeout: float = 900.0,
        poll_interval: float = 2.0,
    ) -> Path:
        client = self._ensure_client()

        response = await client.post(
            f"/reports/{format}",
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        self._handle_response(response)
        queued = response.json()
        report_id = queued["reportId"]

        # an identical report still in storage comes back DONE, with nothing to wait for
        report = queued
        status = queued.get("status", "PENDING")
        elapsed = 0.0
        while status == "PENDING" and elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            response = await client.get(f"/reports/{report_id}")
            self._handle_response(response)
            report = response.json()
            status = report["status"]

        if status == "FAILED":
            raise MiviaError(f"Report {report_id} failed: {report.get('error')}")
        if status == "CANCELLED":
            # the server keeps one report per user; a newer request replaced this one
            raise MiviaError(
                f"Report {report_id} was cancelled by a newer report request"
            )
        if status != "DONE":
            raise JobTimeoutError(f"Report {report_id} not ready within {timeout}s")

        response = await client.get(f"/reports/{report_id}/download")
        self._handle_response(response)
        url = response.json().get("url")
        if not url:
            raise MiviaError(f"Report {report_id} is no longer available")

        out = Path(output_path)
        # a plain client: the presigned URL must not carry the API auth header
        async with httpx.AsyncClient(timeout=self._timeout, proxy=self._proxy) as raw:
            async with raw.stream("GET", url) as file:
                file.raise_for_status()
                with out.open("wb") as sink:
                    async for chunk in file.aiter_bytes():
                        sink.write(chunk)
        return out

    async def analyze(
        self,
        file_paths: list[Path | str],
        model_id: UUID,
        customization_id: UUID | None = None,
        wait: bool = True,
        timeout: float = 300.0,
    ) -> list[JobDto]:
        """
        Upload images, create jobs, optionally wait for completion.

        Args:
            file_paths: List of image paths.
            model_id: Model UUID.
            customization_id: Optional customization UUID.
            wait: Wait for completion.
            timeout: Max wait time in seconds.

        Returns:
            List of job DTOs.
        """
        images = await self.upload_images(file_paths)
        jobs = await self.create_jobs(
            image_ids=[img.id for img in images],
            model_id=model_id,
            customization_id=customization_id,
        )

        if wait:
            jobs = await self.wait_for_jobs(
                [j.id for j in jobs],
                timeout=timeout,
            )

        return jobs

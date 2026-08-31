from uuid import uuid4

import pytest
from pytest_httpx import HTTPXMock

from mivia import MiviaClient, deep_merge


def test_deep_merge_basic() -> None:
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    patch = {"b": {"d": 99, "e": 4}, "f": 5}
    assert deep_merge(base, patch) == {
        "a": 1,
        "b": {"c": 2, "d": 99, "e": 4},
        "f": 5,
    }


def test_deep_merge_does_not_mutate_inputs() -> None:
    base = {"a": {"b": 1}}
    patch = {"a": {"c": 2}}
    deep_merge(base, patch)
    assert base == {"a": {"b": 1}}
    assert patch == {"a": {"c": 2}}


def test_deep_merge_lists_replace_not_concat() -> None:
    base = {"items": [1, 2, 3], "keep": "yes"}
    patch = {"items": [9]}
    assert deep_merge(base, patch) == {"items": [9], "keep": "yes"}


def test_deep_merge_patch_wins_on_type_mismatch() -> None:
    base = {"x": {"deep": True}}
    patch = {"x": "scalar"}
    assert deep_merge(base, patch) == {"x": "scalar"}


@pytest.mark.asyncio
async def test_create_jobs_passes_override(
    httpx_mock: HTTPXMock, api_key: str, base_url: str
) -> None:
    image_id = uuid4()
    model_id = uuid4()
    customization_id = uuid4()
    override = {"thresholds": {"min_area": 0.05}}

    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/jobs",
        json=[],
    )

    async with MiviaClient(api_key=api_key, base_url=base_url) as client:
        await client.create_jobs(
            image_ids=[image_id],
            model_id=model_id,
            customization_id=customization_id,
            customization_config_override=override,
        )

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    body = requests[0].read().decode()
    assert "customizationConfigOverride" in body
    assert "min_area" in body


@pytest.mark.asyncio
async def test_get_resolved_customization_config(
    httpx_mock: HTTPXMock, api_key: str, base_url: str
) -> None:
    customization_id = uuid4()
    resolved = {"thresholds": {"min_area": 0.01}, "PIPELINE": "default"}
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/admin/customizations/groups/{customization_id}/resolved-settings",
        json=resolved,
    )

    async with MiviaClient(api_key=api_key, base_url=base_url) as client:
        result = await client.get_resolved_customization_config(customization_id)

    assert result == resolved


@pytest.mark.asyncio
async def test_get_recent_job_ids_parses_plain_array(
    httpx_mock: HTTPXMock, api_key: str, base_url: str
) -> None:
    job_id = uuid4()
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/jobs?idOnly=true&source=API&since=1h",
        json=[{"id": str(job_id)}],
    )

    async with MiviaClient(api_key=api_key, base_url=base_url) as client:
        result = await client.get_recent_job_ids()

    assert result == [job_id]


@pytest.mark.asyncio
async def test_create_jobs_without_override_omits_field(
    httpx_mock: HTTPXMock, api_key: str, base_url: str
) -> None:
    httpx_mock.add_response(method="POST", url=f"{base_url}/jobs", json=[])

    async with MiviaClient(api_key=api_key, base_url=base_url) as client:
        await client.create_jobs(
            image_ids=[uuid4()],
            model_id=uuid4(),
            customization_id=uuid4(),
        )

    body = httpx_mock.get_requests()[0].read().decode()
    assert "customizationConfigOverride" not in body

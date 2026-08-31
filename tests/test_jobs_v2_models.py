from uuid import uuid4

from mivia import JobDto, JobStatusDto
from mivia.models import JobListResponse

JOB_ID = str(uuid4())
IMAGE_ID = str(uuid4())
MODEL_ID = str(uuid4())
RESULT_ID = str(uuid4())
CUSTOMIZATION_ID = str(uuid4())
ISO = "2026-01-01T00:00:00.000Z"

LIST_ITEM = {
    "id": JOB_ID,
    "imageId": IMAGE_ID,
    "modelId": MODEL_ID,
    "resultId": RESULT_ID,
    "status": "CACHED",
    "hasResults": True,
    "outdated": False,
    "withMasks": True,
    "createdAt": ISO,
    "startedAt": ISO,
    "finishedAt": None,
    "modelVersion": "1.2.3",
    "image": {"orginalFilename": "sample.png", "createdAt": ISO},
    "customizationId": CUSTOMIZATION_ID,
    "userFeedback": {"rating": 4, "comment": None},
    "masksPending": 2,
    "masksSubmitted": 1,
    "result": {"feedback": [{"name": "ok", "value": True, "score": 0.9}]},
}

DETAIL = {
    **LIST_ITEM,
    "source": "WEB",
    "model": {"displayName": "Grain Size"},
    "image": {"id": IMAGE_ID, "orginalFilename": "sample.png", "createdAt": ISO},
    "imageUrls": {"displayUrl": "https://s/d", "originalUrl": "https://s/o"},
    "masks": [
        {
            "id": 1,
            "parentId": None,
            "label": "pore",
            "filename": "m.png",
            "isSubmitted": False,
        }
    ],
    "customization": {
        "config": {"a": 1},
        "template": {"nameEn": "En", "nameDe": "De", "config": None},
    },
    "result": {
        "id": RESULT_ID,
        "feedback": None,
        "results": [{"type": "image", "filename": "r.png"}],
    },
}


def test_list_response_parses() -> None:
    response = JobListResponse.model_validate(
        {
            "data": [LIST_ITEM],
            "pagination": {"total": 1, "page": 1, "pageSize": 10, "totalPages": 1},
        }
    )
    job = response.data[0]
    assert job.image_filename == "sample.png"
    assert job.masks_pending == 2
    assert job.user_feedback is not None
    assert job.user_feedback.comment is None
    assert job.results is None


def test_detail_exposes_results_through_the_result_object() -> None:
    job = JobDto.model_validate(DETAIL)
    assert job.results == [{"type": "image", "filename": "r.png"}]
    assert job.image is not None and job.image.id is not None
    assert job.image_urls is not None
    assert job.customization is not None
    assert job.customization.template is not None
    assert job.customization.template.name_en == "En"
    assert job.model is not None and job.model.display_name == "Grain Size"


def test_job_without_image_parses() -> None:
    job = JobDto.model_validate({**LIST_ITEM, "imageId": None, "image": None})
    assert job.image_filename is None
    assert job.image_id is None


def test_status_item_parses() -> None:
    item = JobStatusDto.model_validate(
        {"id": JOB_ID, "status": "PENDING", "resultId": None, "finishedAt": None}
    )
    assert item.status.value == "PENDING"
    assert item.finished_at is None

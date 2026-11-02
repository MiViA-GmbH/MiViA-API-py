from uuid import uuid4

from mivia import ImageDto

PAYLOAD = {
    "id": str(uuid4()),
    "createdAt": "2026-01-01T00:00:00.000Z",
    "filename": "a.png",
    "thumbnail": "a_thumb.png",
    "orginalFilename": "a.png",
}


def test_image_parses_without_validated():
    assert ImageDto.model_validate(PAYLOAD).validated is True


def test_image_keeps_validated_from_server():
    assert ImageDto.model_validate({**PAYLOAD, "validated": False}).validated is False

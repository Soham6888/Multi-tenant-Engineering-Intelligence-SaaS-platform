import base64
import binascii
import json
from uuid import UUID

from pydantic import BaseModel

from app.services.organization_errors import OrganizationError


class Pagination(BaseModel):
    has_more: bool
    next_cursor: str | None = None


class Page[T](BaseModel):
    data: list[T]
    pagination: Pagination


def encode_cursor(scope: str, identifier: UUID) -> str:
    return base64.urlsafe_b64encode(
        json.dumps([scope, str(identifier)], separators=(",", ":")).encode()
    ).decode()


def decode_cursor(cursor: str | None, scope: str) -> UUID | None:
    if cursor is None:
        return None
    try:
        values = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
        if not isinstance(values, list) or len(values) != 2 or values[0] != scope:
            raise ValueError("Invalid scope")
        return UUID(values[1])
    except (ValueError, TypeError, AttributeError, binascii.Error) as exc:
        raise OrganizationError(422, "INVALID_CURSOR", "Pagination cursor is invalid") from exc


def paginate[T: BaseModel](data: list[T], limit: int, scope: str, ids: list[UUID]) -> Page[T]:
    has_more = len(data) > limit
    return Page(
        data=data[:limit],
        pagination=Pagination(
            has_more=has_more,
            next_cursor=encode_cursor(scope, ids[limit - 1]) if has_more else None,
        ),
    )

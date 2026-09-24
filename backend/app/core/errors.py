from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


def error_response(request: Request, status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {"code": code, "message": message, "request_id": request.state.request_id}
        },
    )


async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    codes = {404: "RESOURCE_NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
    return error_response(
        request, exc.status_code, codes.get(exc.status_code, "REQUEST_FAILED"), str(exc.detail)
    )


async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Do not echo submitted input: validation errors may contain secrets.
    return error_response(request, 422, "VALIDATION_ERROR", "Request validation failed")

import logging
from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.context import get_request_id

logger = logging.getLogger("yojnasetu.errors")

HTTP_STATUS_TO_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "RESOURCE_NOT_FOUND",
    409: "RESOURCE_CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE"
}


def build_error_response(status_code: int, code: str, message: str, details: any = None) -> JSONResponse:
    req_id = get_request_id()
    payload = {
        "detail": message,
        "error": {
            "code": code,
            "message": message,
            "request_id": req_id,
            "details": details
        }
    }
    return JSONResponse(status_code=status_code, content=payload)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = HTTP_STATUS_TO_CODE.get(exc.status_code, "ERROR")
    msg = str(exc.detail) if exc.detail else "An error occurred."
    logger.warning(f"HTTPException [{exc.status_code} {code}]: {msg}")
    return build_error_response(exc.status_code, code, msg)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"ValidationError: {exc.errors()}")
    formatted_errors = []
    for err in exc.errors():
        loc_str = " -> ".join([str(l) for l in err.get("loc", [])])
        formatted_errors.append({
            "field": loc_str,
            "message": err.get("msg", "Invalid value")
        })
    return build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="UNPROCESSABLE_ENTITY",
        message="Validation failed for the request payload.",
        details=formatted_errors
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(f"SQLAlchemy Database Error: {exc}", exc_info=True)
    return build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="DATABASE_ERROR",
        message="A database operation failed while processing your request. Please try again later."
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.critical(f"Unhandled Exception: {exc}", exc_info=True)
    return build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please contact support if the issue persists."
    )

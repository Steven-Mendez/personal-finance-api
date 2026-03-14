import structlog
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions.base_app_exception import BaseAppException
from app.core.schemas.responses import ErrorDetail, ResponseEnvelope

logger = structlog.get_logger()


def setup_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers for the application."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        envelope = ResponseEnvelope[None](
            status="error",
            error=ErrorDetail(
                message="Validation failed",
                error_code="VALIDATION_ERROR",
                data={"errors": exc.errors()},
            ),
        )
        return JSONResponse(
            status_code=422,
            content=envelope.model_dump(exclude_none=True, mode="json"),
        )

    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(
        request: Request, exc: BaseAppException
    ) -> JSONResponse:
        envelope = ResponseEnvelope[None](
            status="error",
            error=ErrorDetail(
                message=exc.message,
                error_code=exc.error_code,
                data=exc.data,
            ),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=envelope.model_dump(exclude_none=True, mode="json"),
        )

    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled server error occurred",
            url=str(request.url),
            method=request.method,
            error=str(exc),
        )
        envelope = ResponseEnvelope[None](
            status="error",
            error=ErrorDetail(
                message=(
                    "An internal server error occurred. Our team has been notified."
                ),
                error_code="INTERNAL_SERVER_ERROR",
                data={"request_id": correlation_id.get()},
            ),
        )
        return JSONResponse(
            status_code=500,
            content=envelope.model_dump(exclude_none=True, mode="json"),
        )

"""
Global error handler middleware.

This module provides centralized error handling for the FastAPI application.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.lib.exceptions import PDFTransformerError
from src.lib.logging import get_logger
from src.models.errors import ErrorResponse

logger = get_logger(__name__)


async def pdf_transformer_error_handler(
    request: Request,
    exc: PDFTransformerError,
) -> JSONResponse:
    """
    Handle PDFTransformerError exceptions.

    Args:
        request: FastAPI request
        exc: PDFTransformerError exception

    Returns:
        JSON error response
    """
    error_response = ErrorResponse(
        error_type=exc.error_type,
        message=exc.message,
        status_code=exc.status_code,
    )

    # Log error
    logger.warning(
        f"Error {exc.error_type}: {exc.message} " f"(status={exc.status_code})"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


async def generic_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle generic exceptions.

    Args:
        request: FastAPI request
        exc: Generic exception

    Returns:
        JSON error response
    """
    from src.models import ErrorType

    error_response = ErrorResponse(
        error_type=ErrorType.INTERNAL_ERROR,
        message="An internal error occurred. Please try again later.",
        status_code=500,
    )

    # Log full error for debugging (but don't expose to client)
    logger.error(f"Internal error: {type(exc).__name__}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register error handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(PDFTransformerError, pdf_transformer_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)

    logger.info("Error handlers registered")


__all__ = [
    "pdf_transformer_error_handler",
    "generic_error_handler",
    "register_error_handlers",
]

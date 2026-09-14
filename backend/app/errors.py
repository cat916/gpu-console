from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models import ErrorDetail, ErrorResponse, FieldError, Instance

HTTP_ERROR_CODES = {404: "not_found", 405: "method_not_allowed"}


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: list[FieldError] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = ErrorDetail(code=code, message=message, fields=fields or [])


def not_found(instance_id: str) -> ApiError:
    return ApiError(404, "not_found", f"No instance with id {instance_id}")


def name_taken(name: str) -> ApiError:
    return ApiError(
        409,
        "name_taken",
        f"An instance named {name} already exists",
        [FieldError(field="name", message="This name is already in use")],
    )


def invalid_state(instance: Instance, action: str) -> ApiError:
    return ApiError(
        409,
        "invalid_state",
        f"Cannot {action} {instance.name} while it is {instance.status}",
    )


def validation_failed(fields: list[FieldError]) -> ApiError:
    return ApiError(422, "validation_failed", "The request has invalid fields", fields)


def error_response(status_code: int, detail: ErrorDetail) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorResponse(error=detail).model_dump())


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = [
            FieldError(
                field=".".join(str(part) for part in error["loc"] if part != "body") or "body",
                message=error["msg"],
            )
            for error in exc.errors()
        ]
        return error_response(422, validation_failed(fields).detail)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = HTTP_ERROR_CODES.get(exc.status_code, "http_error")
        return error_response(exc.status_code, ErrorDetail(code=code, message=str(exc.detail)))

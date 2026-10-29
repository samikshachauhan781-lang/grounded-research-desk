"""Application errors mapped to HTTP responses."""

from typing import Any


class AppError(Exception):
    """Base application error."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: list[Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class PayloadTooLargeError(AppError):
    code = "PAYLOAD_TOO_LARGE"
    status_code = 413


class DemoModeError(AppError):
    code = "DEMO_MODE"
    status_code = 403


class ModelMismatchError(AppError):
    code = "MODEL_MISMATCH"
    status_code = 422


class EmbeddingError(AppError):
    code = "EMBEDDING_ERROR"
    status_code = 503


class LLMProviderError(AppError):
    code = "LLM_PROVIDER_ERROR"
    status_code = 503


class LLMTimeoutError(AppError):
    code = "LLM_TIMEOUT"
    status_code = 504


class AgentDisabledError(AppError):
    code = "AGENT_DISABLED"
    status_code = 403


class AgentBudgetExceededError(AppError):
    code = "AGENT_BUDGET_EXCEEDED"
    status_code = 504

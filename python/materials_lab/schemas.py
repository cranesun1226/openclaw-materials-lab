from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class WorkerError(Exception):
    code: str
    message: str
    hint: str | None = None
    details: Any | None = None
    retriable: bool = False

    def as_payload(self, *, action: str | None = None, request_id: str | None = None, stderr: str | None = None) -> dict[str, Any]:
        return {
            "ok": False,
            "action": action,
            "requestId": request_id,
            "error": {
                "code": self.code,
                "message": self.message,
                "hint": self.hint,
                "details": self.details,
                "retriable": self.retriable,
                "stderr": stderr,
            },
        }


def success(
    *,
    action: str,
    request_id: str,
    summary: str,
    data: Any,
    artifacts: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": True,
        "action": action,
        "requestId": request_id,
        "summary": summary,
        "data": data,
        "artifacts": artifacts or [],
        "warnings": warnings or [],
    }


def ensure_dict(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkerError("INVALID_PARAMS", f"{field} must be an object.", hint="Pass a JSON object in the tool payload.")
    return value


def ensure_string(value: Any, *, field: str, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise WorkerError("INVALID_PARAMS", f"{field} must be a non-empty string.")
    return value.strip()


def ensure_bool(value: Any, *, field: str, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise WorkerError("INVALID_PARAMS", f"{field} must be a boolean.")
    return value


def ensure_number(value: Any, *, field: str, default: float | None = None) -> float | None:
    if value is None:
        return default
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise WorkerError("INVALID_PARAMS", f"{field} must be numeric.")
    return float(value)


def ensure_string_list(value: Any, *, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise WorkerError("INVALID_PARAMS", f"{field} must be an array of strings.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise WorkerError("INVALID_PARAMS", f"{field} must only contain non-empty strings.")
        result.append(item.strip())
    return result

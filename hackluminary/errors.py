"""Typed errors and error codes used across HackLuminary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCode(str, Enum):
    """Stable error codes intended for CLI and machine-readable output."""

    INVALID_INPUT = "INVALID_INPUT"
    CONFIG_ERROR = "CONFIG_ERROR"
    GIT_ERROR = "GIT_ERROR"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    QUALITY_GATE_FAILED = "QUALITY_GATE_FAILED"
    PARSE_ERROR = "PARSE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"


@dataclass
class HackLuminaryError(Exception):
    """Base exception with typed error code and optional remediation hint."""

    code: ErrorCode
    message: str
    hint: str | None = None

    def __str__(self) -> str:
        if self.hint:
            return f"[{self.code}] {self.message} Hint: {self.hint}"
        return f"[{self.code}] {self.message}"

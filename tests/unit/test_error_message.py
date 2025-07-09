"""Unit tests for ErrorMessage."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    ErrorMessage,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for ErrorMessage will be migrated here.


class TestErrorMessage:
    def test_valid_message(self):
        _ = ErrorMessage(
            error_code=400,
            error_message="Bad request",
            severity="error",
            recoverable=True,
            details={"field": "payload", "issue": "too_large"},
        )

    def test_invalid_severity(self):
        with pytest.raises(InvalidMessageError, match="severity must be one of"):
            _ = ErrorMessage(
                error_code=500,
                error_message="Server error",
                severity="invalid",
            )

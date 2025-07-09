"""Unit tests for ResumeResponse message."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    ResumeResponse,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for ResumeResponse will be migrated here.


class TestResumeResponse:
    def test_valid_accepted_response(self, test_nonce: bytes):
        _ = ResumeResponse(
            status_code=0,
            resume_sequence=10,
            session_id="session-123",
            resume_accepted=True,
            server_nonce=test_nonce,
        )

    def test_rejected_without_error_message(self, test_nonce: bytes):
        with pytest.raises(
            InvalidMessageError, match="error_message required when resume_accepted=False"
        ):
            _ = ResumeResponse(
                status_code=1,
                resume_sequence=10,
                session_id="session-123",
                resume_accepted=False,
                server_nonce=test_nonce,
            )

"""Unit tests for ResumeRequest message."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    ResumeRequest,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for ResumeRequest will be migrated here.


class TestResumeRequest:
    def test_valid_message(self, test_nonce: bytes):
        _ = ResumeRequest(
            client_id="client-123",
            last_sequence_number=5,
            client_nonce=test_nonce
        )

    def test_short_nonce(self):
        with pytest.raises(InvalidMessageError, match="client_nonce must be at least 16 bytes"):
            _ = ResumeRequest(
                client_id="client-123",
                last_sequence_number=5,
                client_nonce=b"short"
            )

"""Unit tests for BatchMessage."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    BatchMessage,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for BatchMessage will be migrated here.

class TestBatchMessage:
    def test_valid_message(self):
        messages: list[dict[str, Any]] = [
            {"type": "data", "content": "message1"},
            {"type": "data", "content": "message2"}
        ]
        _ = BatchMessage(
            messages=messages,
            batch_id="batch-123",
            total_count=2
        )

    def test_too_many_messages(self):
        messages: list[dict[str, Any]] = [{"msg": 1}, {"msg": 2}, {"msg": 3}]
        with pytest.raises(InvalidMessageError, match="messages count cannot exceed total_count"):
            _ = BatchMessage(
                messages=messages,
                batch_id="batch-123",
                total_count=2
            )

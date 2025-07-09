"""Unit tests for CloseMessage."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    CloseMessage,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for CloseMessage will be migrated here.


class TestCloseMessage:
    def test_valid_message(self):
        _ = CloseMessage(
            reason="Client requested disconnect",
            graceful=True,
            final_sequence=100
        )

    def test_empty_reason(self):
        with pytest.raises(InvalidMessageError, match="reason must be a non-empty string"):
            _ = CloseMessage(reason="")

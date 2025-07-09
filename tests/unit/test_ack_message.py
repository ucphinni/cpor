"""Unit tests for AckMessage."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    AckMessage,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for AckMessage will be migrated here.


class TestAckMessage:
    def test_valid_message(self):
        _ = AckMessage(
            ack_sequence=5,
            ack_type="message",
            error_code=None
        )

    def test_invalid_ack_type(self):
        with pytest.raises(InvalidMessageError, match="ack_type must be one of"):
            _ = AckMessage(
                ack_sequence=5,
                ack_type="invalid"
            )

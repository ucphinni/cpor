"""Unit tests for HeartbeatMessage."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    HeartbeatMessage,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for HeartbeatMessage will be migrated here.

class TestHeartbeatMessage:
    def test_valid_message(self):
        _ = HeartbeatMessage(
            heartbeat_id="hb-123",
            client_sequence=5,
            server_sequence=3,
            requires_response=True
        )

    def test_negative_sequences(self):
        with pytest.raises(InvalidMessageError, match="client_sequence must be a non-negative integer"):
            _ = HeartbeatMessage(
                heartbeat_id="hb-123",
                client_sequence=-1,
                server_sequence=3
            )

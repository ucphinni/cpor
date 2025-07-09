"""Unit tests for ConnectResponse message."""

import pytest
import cbor2
from typing import Any, Dict

from cpor.messages import (
    ConnectResponse,
    InvalidMessageError,
    SerializationError,
)

# Existing tests for ConnectResponse will be migrated here.


class TestConnectResponse:
    def test_valid_accepted_response(self, test_server_public_key: bytes):
        _ = ConnectResponse(
            session_id="session-123",
            server_pubkey=test_server_public_key,
            status_code=0,
            server_capabilities=["batch", "resume"],
        )

    def test_valid_rejected_response(self, test_server_public_key: bytes):
        _ = ConnectResponse(
            session_id="session-123",
            server_pubkey=test_server_public_key,
            status_code=1,
            error_message="Authentication failed",
        )

    def test_rejected_without_error_message(self, test_server_public_key: bytes):
        with pytest.raises(
            InvalidMessageError, match="error_message required when status_code"
        ):
            _ = ConnectResponse(
                session_id="session-123",
                server_pubkey=test_server_public_key,
                status_code=1,
            )

    def test_invalid_max_message_size(self, test_server_public_key: bytes):
        with pytest.raises(
            InvalidMessageError, match="max_message_size must be a positive integer"
        ):
            _ = ConnectResponse(
                session_id="session-123",
                server_pubkey=test_server_public_key,
                status_code=0,
                max_message_size=0,
            )

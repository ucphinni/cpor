"""Unit tests for ConnectRequest message."""

import pytest
import cbor2
from typing import Any, Tuple, Dict
import nacl.signing

from cpor.messages import (
    ConnectRequest,
    InvalidMessageError,
    SignatureError,
    SerializationError,
    EXAMPLE_MESSAGES,
)

# Existing tests for ConnectRequest will be migrated here.

class TestConnectRequest:
    def test_valid_message(self, test_public_key: bytes):
        msg: ConnectRequest = ConnectRequest(
            client_id="test-client",
            client_pubkey=test_public_key,
            nonce=b"\x01" * 16,
            capabilities=["batch", "resume"]
        )
        assert msg.version == "CPOR-2"
        assert msg.type == "connect_request"
        assert msg.client_id == "test-client"
        assert msg.client_pubkey == test_public_key
        assert msg.capabilities == ["batch", "resume"]

    def test_empty_client_id(self, test_public_key: bytes):
        with pytest.raises(InvalidMessageError, match="client_id must be a non-empty string"):
            _ = ConnectRequest(client_id="", client_pubkey=test_public_key, nonce=b"\x01" * 16)

    def test_invalid_public_key_length(self):
        with pytest.raises(InvalidMessageError, match="client_pubkey must be 32 bytes"):
            _ = ConnectRequest(client_id="test", client_pubkey=b"\x01" * 31, nonce=b"\x01" * 16)

    def test_invalid_capabilities_type(self, test_public_key: bytes):
        with pytest.raises(InvalidMessageError, match="capabilities must be a list"):
            _ = ConnectRequest(
                client_id="test",
                client_pubkey=test_public_key,
                nonce=b"\x01" * 16,
                capabilities="invalid"  # type: ignore
            )

    def test_example_message(self):
        example_data: dict[str, Any] = EXAMPLE_MESSAGES["ConnectRequest"]
        _ = ConnectRequest.from_dict(example_data)
        # Only check that parsing does not raise

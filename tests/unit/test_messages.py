# CPOR-CI-TOKEN-20250707-001
"""Unit tests for CPOR protocol message schemas and serialization."""

import pytest
import cbor2
from typing import Any, Tuple, Dict, Type
import nacl.signing

from cpor.messages import (
    ConnectRequest,
    ConnectResponse,
    GenericMessage,
    ResumeRequest,
    ResumeResponse,
    BatchMessage,
    HeartbeatMessage,
    CloseMessage,
    ErrorMessage,
    parse_message,
    AckMessage,
    EXAMPLE_MESSAGES,
    InvalidMessageError,
    SignatureError,
    SerializationError,
    BaseMessage,
)


class TestBaseMessage:
    """Test the base message functionality."""
    
    def test_version_validation(self):
        """Test that version field is validated."""
        with pytest.raises(InvalidMessageError, match="Invalid protocol version"):
            _: ConnectRequest = ConnectRequest(
                version="CPOR-1",
                client_id="test",
                client_pubkey=b"\x01" * 32,
                nonce=b"\x01" * 16
            )
    
    def test_to_dict(self, test_public_key: bytes) -> None:
        """Test dictionary conversion."""
        msg: ConnectRequest = ConnectRequest(
            client_id="test-client",
            client_pubkey=test_public_key,
            nonce=b"\x01" * 16,
            capabilities=["batch"]
        )
        data: dict[str, Any] = msg.to_dict()
        
        assert data["version"] == "CPOR-2"
        assert data["type"] == "connect_request"
        assert data["client_id"] == "test-client"
        assert data["client_pubkey"] == test_public_key
        assert data["capabilities"] == ["batch"]
    
    def test_cbor_serialization_roundtrip(self, test_public_key: bytes):
        """Test CBOR serialization and deserialization."""
        original: ConnectRequest = ConnectRequest(
            client_id="test-client",
            client_pubkey=test_public_key,
            nonce=b"\x01" * 16,
            capabilities=["batch", "resume"]
        )
        
        # Serialize to CBOR
        cbor_data: bytes = original.to_cbor()
        assert isinstance(cbor_data, bytes)
        
        # Deserialize from CBOR
        restored: ConnectRequest = ConnectRequest.from_cbor(cbor_data)
        assert restored == original
    
    def test_from_dict(self, test_public_key: bytes):
        """Test creating message from dictionary."""
        data: dict[str, Any] = {
            "version": "CPOR-2",
            "type": "connect_request",
            "client_id": "test-client",
            "client_pubkey": test_public_key,
            "nonce": b"\x01" * 16,
            "capabilities": ["batch"]
        }
        
        msg: ConnectRequest = ConnectRequest.from_dict(data)
        assert msg.client_id == "test-client"
        assert msg.client_pubkey == test_public_key
        assert msg.capabilities == ["batch"]
    
    def test_signature_roundtrip(self, test_public_key: bytes, ed25519_keypair: Tuple[nacl.signing.SigningKey, nacl.signing.VerifyKey]):
        """Test Ed25519 signing and verification."""
        signing_key, verify_key = ed25519_keypair
        
        msg: ConnectRequest = ConnectRequest(
            client_id="test-client",
            client_pubkey=test_public_key,
            nonce=b"\x01" * 16
        )
        
        # Sign the message
        signature: bytes = msg.sign(signing_key)
        assert isinstance(signature, bytes)
        assert len(signature) == 64  # Ed25519 signature length
        
        # Verify the signature
        assert msg.verify_signature(signature, verify_key) is True
        
        # Verify that a different message fails verification
        different_msg: ConnectRequest = ConnectRequest(
            client_id="different-client",
            client_pubkey=test_public_key,
            nonce=b"\x01" * 16
        )
        assert different_msg.verify_signature(signature, verify_key) is False
    
    def test_invalid_signature_verification(self):
        msg = ConnectRequest(client_id="test-client", client_pubkey=b"\x01" * 32, nonce=b"valid_nonce_16bytes")
        corrupted_signature = b"\x00" * 64  # Invalid signature
        verify_key = nacl.signing.VerifyKey(b"\x01" * 32)
        assert msg.verify_signature(corrupted_signature, verify_key) is False


class TestConnectRequest:
    """Test ConnectRequest message validation and serialization."""
    
    def test_valid_message(self, test_public_key: bytes):
        """Test creating a valid ConnectRequest."""
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
        """Test that empty client_id is rejected."""
        with pytest.raises(InvalidMessageError, match="client_id must be a non-empty string"):
            _ = ConnectRequest(client_id="", client_pubkey=test_public_key, nonce=b"\x01" * 16)
    
    def test_invalid_public_key_length(self):
        """Test that invalid public key length is rejected."""
        with pytest.raises(InvalidMessageError, match="client_pubkey must be 32 bytes"):
            _ = ConnectRequest(client_id="test", client_pubkey=b"\x01" * 31, nonce=b"\x01" * 16)
    
    def test_invalid_capabilities_type(self, test_public_key: bytes):
        """Test that invalid capabilities type is rejected."""
        with pytest.raises(InvalidMessageError, match="capabilities must be a list"):
            _ = ConnectRequest(
                client_id="test",
                client_pubkey=test_public_key,
                nonce=b"\x01" * 16,
                capabilities="invalid"  # type: ignore
            )
    
    def test_example_message(self):
        """Test the example message from the module."""
        example_data: dict[str, Any] = EXAMPLE_MESSAGES["ConnectRequest"]
        _ = ConnectRequest.from_dict(example_data)
        # Only check that parsing does not raise


class TestConnectResponse:
    """Test ConnectResponse message validation and serialization."""
    
    def test_valid_accepted_response(self, test_server_public_key: bytes):
        """Test creating a valid accepted ConnectResponse."""
        _ = ConnectResponse(
            session_id="session-123",
            server_pubkey=test_server_public_key,
            status_code=0,
            server_capabilities=["batch", "resume"]
        )
        
    def test_valid_rejected_response(self, test_server_public_key: bytes):
        """Test creating a valid rejected ConnectResponse."""
        _ = ConnectResponse(
            session_id="session-123",
            server_pubkey=test_server_public_key,
            status_code=1,
            error_message="Authentication failed"
        )
        
    def test_rejected_without_error_message(self, test_server_public_key: bytes):
        """Test that rejected response requires error message."""
        with pytest.raises(InvalidMessageError, match="error_message required when status_code"):
            _ = ConnectResponse(
                session_id="session-123",
                server_pubkey=test_server_public_key,
                status_code=1
            )
    def test_invalid_max_message_size(self, test_server_public_key: bytes):
        """Test that invalid max_message_size is rejected."""
        with pytest.raises(InvalidMessageError, match="max_message_size must be a positive integer"):
            _ = ConnectResponse(
                session_id="session-123",
                server_pubkey=test_server_public_key,
                status_code=0,
                max_message_size=0
            )


class TestGenericMessage:
    """Test GenericMessage validation and serialization."""
    
    def test_valid_message(self):
        """Test creating a valid GenericMessage."""
        _ = GenericMessage(
            sequence_number=1,
            payload=b"Hello, CPOR!",
            message_type="data",
            priority=5,
            requires_ack=True
        )
        
    def test_negative_sequence_number(self):
        """Test that negative sequence number is rejected."""
        with pytest.raises(InvalidMessageError, match="sequence_number must be a non-negative integer"):
            _ = GenericMessage(
                sequence_number=-1,
                payload=b"test"
            )
    def test_invalid_payload_type(self):
        """Test that non-bytes payload is rejected."""
        with pytest.raises(InvalidMessageError, match="payload must be bytes"):
            _ = GenericMessage(
                sequence_number=1,
                payload="not bytes"  # type: ignore
            )


class TestResumeRequest:
    """Test ResumeRequest validation and serialization."""
    
    def test_valid_message(self, test_nonce: bytes):
        """Test creating a valid ResumeRequest."""
        _ = ResumeRequest(
            client_id="client-123",
            last_sequence_number=5,
            client_nonce=test_nonce
        )
    
    def test_short_nonce(self):
        """Test that short nonce is rejected."""
        with pytest.raises(InvalidMessageError, match="client_nonce must be at least 16 bytes"):
            _ = ResumeRequest(
                client_id="client-123",
                last_sequence_number=5,
                client_nonce=b"short"
            )


class TestResumeResponse:
    """Test ResumeResponse validation and serialization."""
    
    def test_valid_accepted_response(self, test_nonce: bytes):
        """Test creating a valid accepted ResumeResponse."""
        _ = ResumeResponse(
            status_code=0,
            resume_sequence=10,
            session_id="session-123",
            resume_accepted=True,
            server_nonce=test_nonce
        )
    
    def test_rejected_without_error_message(self, test_nonce: bytes):
        """Test that rejected response requires error message."""
        with pytest.raises(InvalidMessageError, match="error_message required when resume_accepted=False"):
            _ = ResumeResponse(
                status_code=1,
                resume_sequence=10,
                session_id="session-123",
                resume_accepted=False,
                server_nonce=test_nonce
            )


class TestBatchMessage:
    """Test BatchMessage validation and serialization."""
    
    def test_valid_message(self):
        """Test creating a valid BatchMessage."""
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
        """Test that message count exceeding total_count is rejected."""
        messages: list[dict[str, Any]] = [{"msg": 1}, {"msg": 2}, {"msg": 3}]
        with pytest.raises(InvalidMessageError, match="messages count cannot exceed total_count"):
            _ = BatchMessage(
                messages=messages,
                batch_id="batch-123",
                total_count=2
            )


class TestHeartbeatMessage:
    """Test HeartbeatMessage validation and serialization."""
    
    def test_valid_message(self):
        """Test creating a valid HeartbeatMessage."""
        _ = HeartbeatMessage(
            heartbeat_id="hb-123",
            client_sequence=5,
            server_sequence=3,
            requires_response=True
        )
        
    def test_negative_sequences(self):
        """Test that negative sequence numbers are rejected."""
        with pytest.raises(InvalidMessageError, match="client_sequence must be a non-negative integer"):
            _ = HeartbeatMessage(
                heartbeat_id="hb-123",
                client_sequence=-1,
                server_sequence=3
            )


class TestCloseMessage:
    """Test CloseMessage validation and serialization."""
    
    def test_valid_message(self):
        """Test creating a valid CloseMessage."""
        _ = CloseMessage(
            reason="Client requested disconnect",
            graceful=True,
            final_sequence=100
        )
        
    def test_empty_reason(self):
        """Test that empty reason is rejected."""
        with pytest.raises(InvalidMessageError, match="reason must be a non-empty string"):
            _ = CloseMessage(reason="")


class TestAckMessage:
    """Test AckMessage validation and serialization."""
    
    def test_valid_message(self):
        """Test creating a valid AckMessage."""
        _ = AckMessage(
            ack_sequence=5,
            ack_type="message",
            error_code=None
        )
        
    def test_invalid_ack_type(self):
        """Test that invalid ack_type is rejected."""
        with pytest.raises(InvalidMessageError, match="ack_type must be one of"):
            _ = AckMessage(
                ack_sequence=5,
                ack_type="invalid"
            )


class TestErrorMessage:
    """Test ErrorMessage validation and serialization."""
    
    def test_valid_message(self):
        """Test creating a valid ErrorMessage."""
        _ = ErrorMessage(
            error_code=400,
            error_message="Bad request",
            severity="error",
            recoverable=True,
            details={"field": "payload", "issue": "too_large"}
        )
        
    def test_invalid_severity(self):
        """Test that invalid severity is rejected."""
        with pytest.raises(InvalidMessageError, match="severity must be one of"):
            _ = ErrorMessage(
                error_code=500,
                error_message="Server error",
                severity="invalid"
            )


class TestMessageParsing:
    """Test the parse_message utility function."""
    
    def test_parse_connect_request(self, test_public_key: bytes):
        """Test parsing a ConnectRequest from CBOR."""
        original: ConnectRequest = ConnectRequest(
            client_id="test-client",
            client_pubkey=test_public_key,
            nonce=b"\x01" * 16
        )
        cbor_data: bytes = original.to_cbor()
        parsed = parse_message(cbor_data)
        assert isinstance(parsed, ConnectRequest)
        assert parsed == original

    def test_parse_generic_message(self):
        """Test parsing a GenericMessage from CBOR."""
        original: GenericMessage = GenericMessage(
            sequence_number=1,
            payload=b"test payload"
        )
        cbor_data: bytes = original.to_cbor()
        parsed = parse_message(cbor_data)
        assert isinstance(parsed, GenericMessage)
        assert parsed == original
    
    def test_parse_invalid_cbor(self):
        """Test that invalid CBOR data raises SerializationError."""
        with pytest.raises(SerializationError, match="Failed to decode CBOR"):
            _ = parse_message(b"invalid cbor data")
    
    def test_parse_unknown_message_type(self):
        """Test that unknown message types raise InvalidMessageError."""
        # Create CBOR data that doesn't match any known message pattern
        unknown_data: dict[str, Any] = {"unknown_field": "value", "version": "CPOR-2"}
        cbor_data: bytes = cbor2.dumps(unknown_data)
        
        with pytest.raises(InvalidMessageError, match="Cannot determine message type"):
            _ = parse_message(cbor_data)
    
    def test_parse_message_valid_type(self):
        valid_data = cbor2.dumps({"type": "connect_request", "client_id": "123", "client_pubkey": b"a" * 32, "nonce": b"valid_nonce_16bytes"})
        message = parse_message(valid_data)
        assert isinstance(message, ConnectRequest)

    def test_parse_message_invalid_type(self):
        invalid_data = cbor2.dumps({"type": "UnknownType", "version": 1})
        with pytest.raises(InvalidMessageError):
            parse_message(invalid_data)

    def test_parse_message_non_dict(self):
        non_dict_data = cbor2.dumps(["type", "ConnectRequest"])
        with pytest.raises(SerializationError):
            parse_message(non_dict_data)


class TestExampleMessages:
    """Test that all example messages are valid."""
    
    def test_all_examples_parse(self):
        """Test that all example messages can be parsed successfully."""
        for msg_type, example_data in EXAMPLE_MESSAGES.items():
            # Create message from example data
            message_class = globals()[msg_type]
            msg = message_class.from_dict(example_data)
            
            # Verify round-trip serialization
            cbor_data = msg.to_cbor()
            restored = message_class.from_cbor(cbor_data)
            assert restored == msg
            
            # Verify it can be parsed generically
            parsed = parse_message(cbor_data)
            assert isinstance(parsed, message_class)
            assert parsed == msg


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_cbor_serialization_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of CBOR serialization errors."""
        msg: ConnectRequest = ConnectRequest(client_id="test", client_pubkey=b"\x01" * 32, nonce=b"\x01" * 16)
        # Mock cbor2.dumps to raise an exception
        def mock_dumps(data: Any) -> None:
            raise Exception("Mock CBOR error")
        monkeypatch.setattr("cbor2.dumps", mock_dumps)
        with pytest.raises(SerializationError, match="Failed to serialize message to CBOR"):
            _ = msg.to_cbor()

    def test_signature_error_handling(self, test_public_key: bytes) -> None:
        """Test handling of signature errors."""
        msg: ConnectRequest = ConnectRequest(client_id="test", client_pubkey=test_public_key, nonce=b"\x01" * 16)
        # Test with invalid signing key type
        with pytest.raises(SignatureError, match="Failed to sign message"):
            _ = msg.sign("not a signing key")  # type: ignore
    
    def test_none_value_filtering(self, test_public_key: bytes) -> None:
        """Test that None values are filtered from dictionary representation."""
        msg: ConnectRequest = ConnectRequest(
            client_id="test",
            client_pubkey=test_public_key,
            nonce=b"\x01" * 16,
            message_id=None  # This should be filtered out
        )
        
        data: dict[str, Any] = msg.to_dict()
        assert "message_id" not in data
        assert "client_id" in data
        assert "client_pubkey" in data


# Test for lines 88-97
@pytest.mark.parametrize("input_data, expected_exception", [
    (b"invalid_cbor", SerializationError),
    (cbor2.dumps("not_a_dict"), SerializationError),
])
def test_deserialize_cbor_exceptions(input_data: bytes, expected_exception: Type[Exception]):
    with pytest.raises(expected_exception):
        BaseMessage.from_cbor(input_data)

# Updated test for lines 109-110
@pytest.mark.parametrize("input_data", [
    {"version": "CPOR-2", "type": None},
    {"version": "CPOR-2", "type": "invalid_type"},
])
def test_invalid_message_type_error(input_data: Dict[str, Any]):
    with pytest.raises(InvalidMessageError):
        ConnectRequest.from_dict(input_data)

# Test for lines 163, 169, 172, 175, 177
@pytest.mark.parametrize("invalid_field_data", [
    {"client_id": "", "client_pubkey": b"", "nonce": b""},
    {"client_pubkey": b"short", "nonce": b"short"},
])
def test_connect_request_field_validation(invalid_field_data: Dict[str, Any]):
    with pytest.raises(InvalidMessageError):
        ConnectRequest(**invalid_field_data)

# Test for lines 208, 211, 214, 217, 226, 229
@pytest.mark.parametrize("invalid_response_data", [
    {"session_id": "", "server_pubkey": b""},
    {"server_pubkey": b"short"},
    {"status_code": 1, "error_message": None},
])
def test_connect_response_field_validation(invalid_response_data: Dict[str, Any]):
    with pytest.raises(InvalidMessageError):
        ConnectResponse(**invalid_response_data)

# Test for lines 253, 259, 284, 287, 290, 293
@pytest.mark.parametrize("invalid_generic_data", [
    {"sequence_number": -1},
    {"payload": "not_bytes"},
])
def test_generic_message_field_validation(invalid_generic_data: Dict[str, Any]):
    with pytest.raises(InvalidMessageError):
        GenericMessage(**invalid_generic_data)

# Tests for structural and explicit `_infer_message_type` branches
@pytest.mark.parametrize("data,expected", [
    # Explicit type mapping
    ("connect_request", ConnectRequest),
    ("connect_response", ConnectResponse),
    ("generic", GenericMessage),
    ("resume_request", ResumeRequest),
    ("resume_response", ResumeResponse),
    ("batch", BatchMessage),
    ("heartbeat", HeartbeatMessage),
    ("close", CloseMessage),
    ("ack", AckMessage),
    ("error", ErrorMessage),
])
def test_parse_message_all_branches(data: str, expected: Type[BaseMessage]):
    required_fields = {
        "connect_request": {"client_id": "test", "client_pubkey": b"x"*32, "nonce": b"n"*16},
        "connect_response": {"session_id": "session", "server_pubkey": b"y"*32, "status_code": 0},
        "generic": {"sequence_number": 1, "payload": b"payload"},
        "resume_request": {"client_id": "test", "last_sequence_number": 0, "client_nonce": b"n"*16},
        "resume_response": {"status_code": 0, "resume_sequence": 0, "session_id": "session", "server_nonce": b"n"*16, "error_message": "error"},
        "batch": {"messages": [{"type": "data"}], "batch_id": "batch", "total_count": 1},
        "heartbeat": {"heartbeat_id": "hb", "client_sequence": 0, "server_sequence": 0},
        "close": {"reason": "reason", "graceful": True},
        "ack": {"ack_sequence": 0, "ack_type": "message"},
        "error": {"error_code": 400, "error_message": "error"},
    }
    cbor_data = cbor2.dumps({"type": data, **required_fields[data]})
    parsed_message = parse_message(cbor_data)
    assert isinstance(parsed_message, expected)

# Test parse_message unknown data
@pytest.mark.parametrize("data", [
    {"foo": "bar"},
    {"unknown_field": "value"},
])
def test_parse_message_raises(data: Dict[str, Any]):
    cbor_data = cbor2.dumps(data)
    with pytest.raises(InvalidMessageError, match="Cannot determine message type"):
        parse_message(cbor_data)

# Test from_dict invalid data TypeError handling
def test_from_dict_type_error():
    with pytest.raises(InvalidMessageError, match="client_id must be a non-empty string"):
        ConnectRequest.from_dict({})

# Test sign exception handling when underlying sign fails
def test_sign_raises_signature_error():
    msg = ConnectRequest(client_id="c", client_pubkey=b"x"*32, nonce=b"n"*16)
    class BadSigner:
        def sign(self, data: bytes) -> None:
            raise Exception("bad sign")
    with pytest.raises(SignatureError, match="Failed to sign message"):
        msg.sign(BadSigner())  # type: ignore

def test_verify_signature_raises():
    msg = ConnectRequest(client_id="c", client_pubkey=b"x"*32, nonce=b"n"*16)
    class BadVerifier:
        def verify(self, data: bytes, sig: bytes) -> None:
            raise Exception("bad verify")
    with pytest.raises(SignatureError, match="Failed to verify signature"):
        msg.verify_signature(b"sig", BadVerifier())  # type: ignore


"""
CPOR Protocol Message Schemas and Serialization

This module defines all CBOR message types for the CPOR protocol with Ed25519 signing
support. All messages are immutable dataclasses with CBOR serialization/deserialization
and cryptographic signature capabilities.

Protocol Version: CPOR-2
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar, cast
import cbor2
import nacl.signing
from nacl.exceptions import BadSignatureError

# Type variable for message classes
T = TypeVar('T', bound='BaseMessage')

logger = logging.getLogger(__name__)


class CPORMessageError(Exception):
    """Base exception for CPOR message errors."""
    pass


class InvalidMessageError(CPORMessageError):
    """Raised when message validation fails."""
    pass


class SignatureError(CPORMessageError):
    """Raised when signature verification fails."""
    pass


class SerializationError(CPORMessageError):
    """Raised when CBOR serialization/deserialization fails."""
    pass


@dataclass(frozen=True)
class BaseMessage:
    """Base class for all CPOR protocol messages."""
    
    # Optional fields with defaults - these come first in base class
    version: str = field(default="CPOR-2")
    message_id: Optional[str] = field(default=None)
    timestamp: Optional[int] = field(default=None)
    
    def __post_init__(self) -> None:
        """Validate message fields after initialization."""
        if self.version != "CPOR-2":
            raise InvalidMessageError(f"Invalid protocol version: {self.version}")
        self._validate_fields()
    
    def _validate_fields(self) -> None:
        """Validate message-specific fields. Override in subclasses."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        result: Dict[str, Any] = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        return result
    
    def to_cbor(self) -> bytes:
        """Serialize message to CBOR bytes."""
        try:
            data = self.to_dict()
            return cbor2.dumps(data)
        except Exception as e:
            raise SerializationError(f"Failed to serialize message to CBOR: {e}")
    
    @classmethod
    def from_cbor(cls: Type[T], data: bytes) -> T:
        """Deserialize message from CBOR bytes."""
        try:
            decoded = cbor2.loads(data)
            if not isinstance(decoded, dict):
                raise SerializationError("Failed to decode CBOR data: CBOR data must be a dictionary")
            # Cast to proper type for type checker
            decoded_dict = cast(Dict[str, Any], decoded)
            return cls.from_dict(decoded_dict)
        except cbor2.CBORDecodeError as e:
            raise SerializationError(f"Failed to decode CBOR data: {e}")
        except InvalidMessageError:
            raise  # Let InvalidMessageError propagate for test compatibility
        except Exception as e:
            raise SerializationError(f"Failed to deserialize message from CBOR: {e}")
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create message instance from dictionary."""
        try:
            # Filter out unknown fields and None values
            valid_fields: Dict[str, Any] = {}
            for field_name in cls.__dataclass_fields__:
                if field_name in data and data[field_name] is not None:
                    valid_fields[field_name] = data[field_name]
            return cls(**valid_fields)
        except TypeError as e:
            raise InvalidMessageError(f"Invalid message data: {e}")
    
    def sign(self, signing_key: nacl.signing.SigningKey) -> bytes:
        """Sign the message using Ed25519 and return signature."""
        try:
            message_bytes = self.to_cbor()
            signature = signing_key.sign(message_bytes)
            return signature.signature
        except Exception as e:
            raise SignatureError(f"Failed to sign message: {e}")
    
    def verify_signature(self, signature: bytes, verify_key: nacl.signing.VerifyKey) -> bool:
        """Verify Ed25519 signature for this message."""
        try:
            message_bytes = self.to_cbor()
            verify_key.verify(message_bytes, signature)
            return True
        except BadSignatureError:
            return False
        except Exception as e:
            raise SignatureError(f"Failed to verify signature: {e}")


@dataclass(frozen=True)
class ConnectRequest(BaseMessage):
    """Initial connection request message."""
    
    # Message type identifier (per spec)
    type: str = field(default="connect_request")
    
    # Required fields (spec + our additions)
    client_id: str = field(default="")
    client_pubkey: bytes = field(default=b"")  # Spec field name
    resume_sequence: int = field(default=0)    # Updated from resume_counter per your note
    nonce: bytes = field(default=b"")          # Anti-replay protection
    registration_flag: bool = field(default=False)  # Registration flow trigger
    
    # Optional fields (spec + our additions)
    protocol_version: str = field(default="CPOR-2")  # Our addition - useful
    capabilities: List[str] = field(default_factory=lambda: [])  # Our addition - useful
    key_storage: Optional[str] = field(default=None)  # "tpm" or "software"
    
    def _validate_fields(self) -> None:
        """Validate ConnectRequest fields."""
        super()._validate_fields()
        
        if self.type != "connect_request":
            raise InvalidMessageError("type must be 'connect_request'")
        
        if not self.client_id:
            raise InvalidMessageError("client_id must be a non-empty string")
        
        if not self.client_pubkey:
            raise InvalidMessageError("client_pubkey must be non-empty bytes")
        
        if len(self.client_pubkey) != 32:
            raise InvalidMessageError("client_pubkey must be 32 bytes for Ed25519")
        
        if not self.nonce:
            raise InvalidMessageError("nonce must be non-empty bytes")
        
        if len(self.nonce) < 16:
            raise InvalidMessageError("nonce must be at least 16 bytes for security")
        
        if self.key_storage is not None and self.key_storage not in ["tpm", "software"]:
            raise InvalidMessageError("key_storage must be 'tpm' or 'software'")
        if self.resume_sequence < 0:
            raise InvalidMessageError("resume_sequence must be a non-negative integer")
        # Enforce capabilities must be a list
        if not isinstance(self.capabilities, list): # type: ignore
            raise InvalidMessageError("capabilities must be a list")


@dataclass(frozen=True)
class ConnectResponse(BaseMessage):
    """Connection response message."""
    
    # Message type identifier (per spec)
    type: str = field(default="connect_response")
    
    # Required fields (spec)
    session_id: str = field(default="")
    server_pubkey: bytes = field(default=b"")  # Spec field name
    accepted: bool = field(default=False)
    resume_sequence: int = field(default=0)    # Updated from resume_counter per your note
    status_code: int = field(default=0)        # Success/error code per spec
    
    # Optional fields (spec + our additions)
    error_message: Optional[str] = field(default=None)
    server_capabilities: List[str] = field(default_factory=lambda: [])  # Our addition - useful
    max_message_size: int = field(default=1048576)  # 1MB default
    ephemeral_pubkey: Optional[bytes] = field(default=None)  # For registration flow
    
    def _validate_fields(self) -> None:
        """Validate ConnectResponse fields."""
        super()._validate_fields()
        
        if self.type != "connect_response":
            raise InvalidMessageError("type must be 'connect_response'")
        
        if not self.session_id:
            raise InvalidMessageError("session_id must be a non-empty string")
        
        if not self.server_pubkey:
            raise InvalidMessageError("server_pubkey must be non-empty bytes")
        
        if len(self.server_pubkey) != 32:
            raise InvalidMessageError("server_pubkey must be 32 bytes for Ed25519")
        
        if self.status_code != 0 and not self.error_message:
            raise InvalidMessageError("error_message required when status_code != 0")
        
        if self.max_message_size <= 0:
            raise InvalidMessageError("max_message_size must be a positive integer")
        
        if self.resume_sequence < 0:
            raise InvalidMessageError("resume_sequence must be a non-negative integer")
        
        if self.ephemeral_pubkey is not None and len(self.ephemeral_pubkey) != 32:
            raise InvalidMessageError("ephemeral_pubkey must be 32 bytes for Ed25519")


@dataclass(frozen=True)
class GenericMessage(BaseMessage):
    """Generic data message with sequence numbering."""
    
    # Message type identifier (per spec)
    type: str = field(default="generic")
    
    # Required fields (spec + our naming preference)
    sequence_number: int = field(default=0)  # We prefer sequence_number over sequence_counter
    payload: bytes = field(default=b"")
    
    # Optional fields (our additions - useful for message handling)
    message_type: str = field(default="data")
    priority: int = field(default=0)  # Our addition - useful for prioritization
    requires_ack: bool = field(default=True)
    
    def _validate_fields(self) -> None:
        """Validate GenericMessage fields."""
        super()._validate_fields()
        
        if self.type != "generic":
            raise InvalidMessageError("type must be 'generic'")
        
        if self.sequence_number < 0:
            raise InvalidMessageError("sequence_number must be a non-negative integer")
        
        if not self.message_type:
            raise InvalidMessageError("message_type must be a non-empty string")
        
        if not isinstance(self.payload, bytes):
            raise InvalidMessageError("payload must be bytes")


@dataclass(frozen=True)
class ResumeRequest(BaseMessage):
    """Request to resume a previous session."""
    
    # Message type identifier (per spec)
    type: str = field(default="resume_request")
    
    # Required fields (spec)
    client_id: str = field(default="")
    last_sequence_number: int = field(default=0)  # Using our preferred naming
    
    # Our additional field (was client_nonce)
    client_nonce: bytes = field(default=b"")
    
    def _validate_fields(self) -> None:
        """Validate ResumeRequest fields."""
        super()._validate_fields()
        
        if self.type != "resume_request":
            raise InvalidMessageError("type must be 'resume_request'")
        
        if not self.client_id:
            raise InvalidMessageError("client_id must be a non-empty string")
        
        if self.last_sequence_number < 0:
            raise InvalidMessageError("last_sequence_number must be a non-negative integer")
        
        if not self.client_nonce:
            raise InvalidMessageError("client_nonce must be non-empty bytes")
        
        if len(self.client_nonce) < 16:
            raise InvalidMessageError("client_nonce must be at least 16 bytes")


@dataclass(frozen=True)
class ResumeResponse(BaseMessage):
    """Response to resume request."""
    
    # Message type identifier (per spec)
    type: str = field(default="resume_response")
    
    # Required fields (spec)
    status_code: int = field(default=0)          # 0 = success, nonzero = error
    resume_sequence: int = field(default=0)      # Server's last acknowledged sequence
    
    # Optional fields (spec + our additions)
    error_message: Optional[str] = field(default=None)
    
    # Our additional fields (useful for session management)
    session_id: str = field(default="")
    resume_accepted: bool = field(default=False)
    server_nonce: bytes = field(default=b"")
    
    def _validate_fields(self) -> None:
        """Validate ResumeResponse fields."""
        super()._validate_fields()
        
        if self.type != "resume_response":
            raise InvalidMessageError("type must be 'resume_response'")
        
        if not self.session_id:
            raise InvalidMessageError("session_id must be a non-empty string")
        
        if self.resume_sequence < 0:
            raise InvalidMessageError("resume_sequence must be a non-negative integer")
        
        if not self.server_nonce:
            raise InvalidMessageError("server_nonce must be non-empty bytes")
        
        if len(self.server_nonce) < 16:
            raise InvalidMessageError("server_nonce must be at least 16 bytes")
        
        if not self.resume_accepted and not self.error_message:
            raise InvalidMessageError("error_message required when resume_accepted=False")


@dataclass(frozen=True)
class BatchMessage(BaseMessage):
    """Batch container for multiple messages."""
    
    # Message type identifier (per spec)
    type: str = field(default="batch")
    
    # Required fields (spec)
    messages: List[Dict[str, Any]] = field(default_factory=lambda: [])
    
    # Our additional fields (useful for batch management)
    batch_id: str = field(default="")
    total_count: int = field(default=0)
    
    def _validate_fields(self) -> None:
        """Validate BatchMessage fields."""
        super()._validate_fields()
        
        if self.type != "batch":
            raise InvalidMessageError("type must be 'batch'")
        
        if not self.batch_id:
            raise InvalidMessageError("batch_id must be a non-empty string")
        
        if self.total_count <= 0:
            raise InvalidMessageError("total_count must be a positive integer")
        
        if len(self.messages) > self.total_count:
            raise InvalidMessageError("messages count cannot exceed total_count")


@dataclass(frozen=True)
class HeartbeatMessage(BaseMessage):
    """Heartbeat/keepalive message."""
    
    # Message type identifier (per spec)
    type: str = field(default="heartbeat")
    
    # Required fields (spec)
    timestamp: Optional[int] = field(default=None)  # ISO8601 or epoch seconds
    
    # Our additional fields (useful for sequence tracking)
    heartbeat_id: str = field(default="")
    client_sequence: int = field(default=0)
    server_sequence: int = field(default=0)
    requires_response: bool = field(default=True)
    
    def _validate_fields(self) -> None:
        """Validate HeartbeatMessage fields."""
        super()._validate_fields()
        
        if self.type != "heartbeat":
            raise InvalidMessageError("type must be 'heartbeat'")
        
        if not self.heartbeat_id:
            raise InvalidMessageError("heartbeat_id must be a non-empty string")
        
        if self.client_sequence < 0:
            raise InvalidMessageError("client_sequence must be a non-negative integer")
        
        if self.server_sequence < 0:
            raise InvalidMessageError("server_sequence must be a non-negative integer")


@dataclass(frozen=True)
class CloseMessage(BaseMessage):
    """Connection close message."""
    
    # Message type identifier (per spec)
    type: str = field(default="close")
    
    # Required fields (spec)
    reason: str = field(default="")
    final_sequence: Optional[int] = field(default=None)  # final_counter in spec
    
    # Our additional field (useful for graceful vs forced close)
    graceful: bool = field(default=True)
    
    def _validate_fields(self) -> None:
        """Validate CloseMessage fields."""
        super()._validate_fields()
        
        if self.type != "close":
            raise InvalidMessageError("type must be 'close'")
        
        if not self.reason:
            raise InvalidMessageError("reason must be a non-empty string")
        
        if self.final_sequence is not None and self.final_sequence < 0:
            raise InvalidMessageError("final_sequence must be a non-negative integer")


@dataclass(frozen=True)
class AckMessage(BaseMessage):
    """Acknowledgment message for received messages."""
    
    # Message type identifier (per spec)
    type: str = field(default="ack")
    
    # Required fields (using our preferred naming)
    ack_sequence: int = field(default=0)  # We prefer ack_sequence over ack_counter
    
    # Our additional fields (useful for ack management)
    ack_type: str = field(default="message")
    error_code: Optional[int] = field(default=None)
    
    def _validate_fields(self) -> None:
        """Validate AckMessage fields."""
        super()._validate_fields()
        
        if self.type != "ack":
            raise InvalidMessageError("type must be 'ack'")
        
        if self.ack_sequence < 0:
            raise InvalidMessageError("ack_sequence must be a non-negative integer")
        
        if not self.ack_type:
            raise InvalidMessageError("ack_type must be a non-empty string")
        
        if self.ack_type not in ["message", "heartbeat", "batch"]:
            raise InvalidMessageError("ack_type must be one of: message, heartbeat, batch")


@dataclass(frozen=True)
class ErrorMessage(BaseMessage):
    """Error message for protocol violations or failures."""
    
    # Message type identifier (per spec)
    type: str = field(default="error")
    
    # Required fields (spec)
    error_code: int = field(default=0)
    error_message: str = field(default="")  # 'message' field in spec
    
    # Our additional fields (useful for error handling)
    severity: str = field(default="error")
    recoverable: bool = field(default=True)
    details: Optional[Dict[str, Any]] = field(default=None)
    
    def _validate_fields(self) -> None:
        """Validate ErrorMessage fields."""
        super()._validate_fields()
        
        if self.type != "error":
            raise InvalidMessageError("type must be 'error'")
        
        if not self.error_message:
            raise InvalidMessageError("error_message must be a non-empty string")
        
        if self.severity not in ["warning", "error", "fatal"]:
            raise InvalidMessageError("severity must be one of: warning, error, fatal")


# Message type registry for deserialization
MESSAGE_TYPES: Dict[str, Type[BaseMessage]] = {
    "ConnectRequest": ConnectRequest,
    "ConnectResponse": ConnectResponse,
    "GenericMessage": GenericMessage,
    "ResumeRequest": ResumeRequest,
    "ResumeResponse": ResumeResponse,
    "BatchMessage": BatchMessage,
    "HeartbeatMessage": HeartbeatMessage,
    "CloseMessage": CloseMessage,
    "AckMessage": AckMessage,
    "ErrorMessage": ErrorMessage,
}


def parse_message(cbor_data: bytes) -> BaseMessage:
    """
    Parse CBOR data into appropriate message type.
    
    Args:
        cbor_data: Raw CBOR bytes
        
    Returns:
        Parsed message instance
        
    Raises:
        SerializationError: If CBOR parsing fails
        InvalidMessageError: If message type is unknown or invalid
    """
    try:
        data = cbor2.loads(cbor_data)
        if not isinstance(data, dict):
            raise SerializationError("Failed to decode CBOR data: CBOR data must be a dictionary")
        data_dict = cast(Dict[str, Any], data)
        message_type = _infer_message_type(data_dict)
        message_class = MESSAGE_TYPES.get(message_type)
        if not message_class:
            raise InvalidMessageError(f"Unknown message type: {message_type}")
        return message_class.from_dict(data_dict)
    except cbor2.CBORDecodeError as e:
        raise SerializationError(f"Failed to decode CBOR data: {e}")
    except InvalidMessageError:
        raise  # Let InvalidMessageError propagate for test compatibility
    except Exception as e:
        raise SerializationError(f"Failed to parse message: {e}")


def _infer_message_type(data: Dict[str, Any]) -> str:
    """
    Infer message type from message data structure.
    
    Args:
        data: Decoded message dictionary
        
    Returns:
        Message type name
        
    Raises:
        InvalidMessageError: If message type cannot be determined
    """
    # Check for explicit type field first (spec compliant)
    if "type" in data:
        type_field = data["type"]
        type_mapping = {
            "connect_request": "ConnectRequest",
            "connect_response": "ConnectResponse", 
            "generic": "GenericMessage",
            "resume_request": "ResumeRequest",
            "resume_response": "ResumeResponse",
            "batch": "BatchMessage",
            "heartbeat": "HeartbeatMessage",
            "close": "CloseMessage",
            "ack": "AckMessage",
            "error": "ErrorMessage",
        }
        if type_field in type_mapping:
            return type_mapping[type_field]
    
    # Fallback to structural detection for backward compatibility
    if "client_id" in data and ("client_pubkey" in data or "public_key" in data):
        return "ConnectRequest"
    elif "session_id" in data and "accepted" in data and ("server_pubkey" in data or "server_public_key" in data):
        return "ConnectResponse"
    elif ("sequence_number" in data or "sequence_counter" in data) and "payload" in data:
        return "GenericMessage"
    elif ("last_sequence_number" in data or "last_received_sequence" in data) and "client_nonce" in data:
        return "ResumeRequest"
    elif ("resume_accepted" in data or "status_code" in data) and ("server_nonce" in data or "resume_sequence" in data):
        return "ResumeResponse"
    elif "messages" in data and "batch_id" in data:
        return "BatchMessage"
    elif "heartbeat_id" in data or ("timestamp" in data and "type" not in data):
        return "HeartbeatMessage"
    elif "reason" in data and ("graceful" in data or "final_sequence" in data):
        return "CloseMessage"
    elif ("ack_sequence" in data or "ack_counter" in data):
        return "AckMessage"
    elif "error_code" in data and ("error_message" in data or "message" in data):
        return "ErrorMessage"
    else:
        raise InvalidMessageError(f"Cannot determine message type from data: {list(data.keys())}")


# Example test vectors for validation
EXAMPLE_MESSAGES: Dict[str, Dict[str, Any]] = {
    "ConnectRequest": {
        "version": "CPOR-2",
        "type": "connect_request",
        "client_id": "client-123",
        "client_pubkey": b"\x01" * 32,
        "resume_sequence": 0,
        "nonce": b"\x01" * 16,
        "registration_flag": False,
        "protocol_version": "CPOR-2",
        "capabilities": ["batch", "resume"],
        "key_storage": "software",
        "message_id": "msg-001",
        "timestamp": 1672531200
    },
    "ConnectResponse": {
        "version": "CPOR-2",
        "type": "connect_response",
        "session_id": "session-456",
        "server_pubkey": b"\x02" * 32,
        "accepted": True,
        "resume_sequence": 0,
        "status_code": 0,
        "server_capabilities": ["batch", "resume", "compression"],
        "max_message_size": 2097152,
        "message_id": "msg-002",
        "timestamp": 1672531201
    },
    "GenericMessage": {
        "version": "CPOR-2",
        "type": "generic",
        "sequence_number": 1,
        "payload": b"Hello, CPOR!",
        "message_type": "data",
        "priority": 0,
        "requires_ack": True,
        "message_id": "msg-003",
        "timestamp": 1672531202
    },
    "HeartbeatMessage": {
        "version": "CPOR-2",
        "type": "heartbeat",
        "heartbeat_id": "hb-001",
        "client_sequence": 5,
        "server_sequence": 3,
        "requires_response": True,
        "message_id": "msg-004",
        "timestamp": 1672531203
    },
    "ErrorMessage": {
        "version": "CPOR-2",
        "type": "error",
        "error_code": 400,
        "error_message": "Invalid message format",
        "severity": "error",
        "recoverable": True,
        "details": {"field": "sequence_number", "expected": "integer"},
        "message_id": "msg-005",
        "timestamp": 1672531204
    }
}

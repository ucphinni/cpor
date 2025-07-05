"""
CPOR Protocol Implementation

A production-ready CBOR Protocol Over Reliable (CPOR) implementation in Python 3.12+
with full async support, Ed25519 signing, and robust connection management.

Protocol Version: CPOR-2
"""

__version__ = "0.1.0"
__protocol_version__ = "CPOR-2"

from .messages import (
    # Base classes and utilities
    BaseMessage,
    parse_message,
    MESSAGE_TYPES,
    EXAMPLE_MESSAGES,
    
    # Message types
    ConnectRequest,
    ConnectResponse,
    GenericMessage,
    ResumeRequest,
    ResumeResponse,
    BatchMessage,
    HeartbeatMessage,
    CloseMessage,
    AckMessage,
    ErrorMessage,
    
    # Exceptions
    CPORMessageError,
    InvalidMessageError,
    SignatureError,
    SerializationError,
)

__all__ = [
    # Version info
    "__version__",
    "__protocol_version__",
    
    # Base classes and utilities
    "BaseMessage",
    "parse_message",
    "MESSAGE_TYPES",
    "EXAMPLE_MESSAGES",
    
    # Message types
    "ConnectRequest",
    "ConnectResponse",
    "GenericMessage",
    "ResumeRequest",
    "ResumeResponse",
    "BatchMessage",
    "HeartbeatMessage",
    "CloseMessage",
    "AckMessage",
    "ErrorMessage",
    
    # Exceptions
    "CPORMessageError",
    "InvalidMessageError",
    "SignatureError",
    "SerializationError",
]

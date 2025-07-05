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

from .config import (
    # Configuration classes
    CPORConfig,
    ConfigManager,
    NetworkConfig,
    CryptoConfig,
    LoggingConfig,
    SecurityConfig,
    PerformanceConfig,
    
    # Configuration utilities
    load_config,
    get_config_manager,
    set_config_manager,
    EXAMPLE_CONFIGS,
    
    # Configuration exceptions
    CPORConfigError,
    ConfigValidationError,
    ConfigLoadError,
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
    
    # Message exceptions
    "CPORMessageError",
    "InvalidMessageError",
    "SignatureError",
    "SerializationError",
    
    # Configuration classes
    "CPORConfig",
    "ConfigManager",
    "NetworkConfig",
    "CryptoConfig",
    "LoggingConfig",
    "SecurityConfig",
    "PerformanceConfig",
    
    # Configuration utilities
    "load_config",
    "get_config_manager",
    "set_config_manager",
    "EXAMPLE_CONFIGS",
    
    # Configuration exceptions
    "CPORConfigError",
    "ConfigValidationError",
    "ConfigLoadError",
]

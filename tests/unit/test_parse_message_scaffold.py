"""Scaffold for parse_message and _infer_message_type tests."""

import pytest
import cbor2
from cpor.messages import (
    parse_message,
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
    InvalidMessageError,
    SerializationError,
)

# TODO: Implement parse_message and _infer_message_type tests here
# - test_invalid_cbor raises SerializationError
# - test_non_dict_data raises SerializationError
# - test_unknown_explicit_type raises InvalidMessageError
# - test_structural_infer for each branch
# - test_unknown_structural_data raises InvalidMessageError

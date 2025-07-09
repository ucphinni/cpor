import pytest
import cbor2
from typing import Any

from cpor.messages import (
    BaseMessage,
    ConnectRequest,
    SerializationError,
    InvalidMessageError,
    SignatureError,
)

# TODO: Implement TestBaseMessage tests here
# - test_version_validation
# - test_to_dict filtering and None removal
# - test_cbor_serialization_roundtrip and from_cbor errors
# - test_from_dict data filtering and type errors
# - test_sign and test_verify_signature exception paths

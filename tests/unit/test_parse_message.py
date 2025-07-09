import pytest
import cbor2
from cpor.messages import parse_message, InvalidMessageError, SerializationError

def test_parse_message_invalid_cbor():
    """Test parse_message with invalid CBOR data."""
    invalid_data = b"not-cbor"
    with pytest.raises(SerializationError, match="Failed to decode CBOR data"):
        parse_message(invalid_data)

def test_parse_message_non_dict():
    """Test parse_message with non-dictionary CBOR data."""
    non_dict_data = cbor2.dumps([1, 2, 3])
    with pytest.raises(SerializationError, match="CBOR data must be a dictionary"):
        parse_message(non_dict_data)

def test_parse_message_unknown_type():
    """Test parse_message with unknown message type."""
    unknown_type_data = cbor2.dumps({"type": "unknown_type"})
    with pytest.raises(InvalidMessageError, match="Unknown message type"):
        parse_message(unknown_type_data)

def test_parse_message_missing_fields():
    """Test parse_message with missing required fields for type inference."""
    missing_fields_data = cbor2.dumps({"unexpected_field": "value"})
    with pytest.raises(InvalidMessageError, match="Cannot determine message type"):
        parse_message(missing_fields_data)

def test_parse_message_general_exception():
    """Test parse_message with unexpected errors."""
    def mock_loads(_):
        raise ValueError("Unexpected error")

    original_loads = cbor2.loads
    cbor2.loads = mock_loads

    try:
        with pytest.raises(SerializationError, match="Failed to parse message"):
            parse_message(b"valid-cbor")
    finally:
        cbor2.loads = original_loads

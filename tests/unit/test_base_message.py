import pytest
from cpor.messages import BaseMessage, InvalidMessageError
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MockMessage(BaseMessage):
    """Mock message class for testing."""
    type: str = "mock"
    required_field: int = 0

def test_from_dict_valid_data():
    """Test from_dict with valid data."""
    data: dict[str, Any] = {"type": "mock", "required_field": 42}
    message = MockMessage.from_dict(data)
    assert message.type == "mock"
    assert message.required_field == 42

def test_from_dict_invalid_data():
    """Test from_dict with invalid data."""
    data: dict[str, Any] = {"type": "mock", "required_field": "not-an-int"}
    with pytest.raises(InvalidMessageError, match="Invalid message data"):
        MockMessage.from_dict(data)

def test_from_dict_missing_field():
    """Test from_dict with missing required field."""
    data: dict[str, Any] = {"type": "mock"}
    with pytest.raises(InvalidMessageError, match="Invalid message data"):
        MockMessage.from_dict(data)

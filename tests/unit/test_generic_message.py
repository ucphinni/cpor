"""Unit tests for GenericMessage."""

import pytest
from cpor.messages import (
    GenericMessage,
    InvalidMessageError,
)


class TestGenericMessage:
    def test_valid_message(self):
        _ = GenericMessage(
            sequence_number=1,
            payload=b"Hello, CPOR!",
            message_type="data",
            priority=5,
            requires_ack=True
        )

    def test_negative_sequence_number(self):
        with pytest.raises(InvalidMessageError, match="sequence_number must be a non-negative integer"):
            _ = GenericMessage(
                sequence_number=-1,
                payload=b"test"
            )

    def test_invalid_payload_type(self):
        with pytest.raises(InvalidMessageError, match="payload must be bytes"):
            _ = GenericMessage(
                sequence_number=1,
                payload="not bytes"  # type: ignore
            )

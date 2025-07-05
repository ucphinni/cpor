"""Test configuration and utilities for CPOR protocol tests."""

import pytest
import nacl.signing
import nacl.utils
from typing import Tuple


@pytest.fixture
def ed25519_keypair() -> Tuple[nacl.signing.SigningKey, nacl.signing.VerifyKey]:
    """Generate a fresh Ed25519 keypair for testing."""
    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key
    return signing_key, verify_key


@pytest.fixture
def test_public_key() -> bytes:
    """Return a 32-byte test public key."""
    return b"\x01" * 32


@pytest.fixture
def test_server_public_key() -> bytes:
    """Return a 32-byte test server public key."""
    return b"\x02" * 32


@pytest.fixture
def test_nonce() -> bytes:
    """Return a 16-byte test nonce."""
    return nacl.utils.random(16)

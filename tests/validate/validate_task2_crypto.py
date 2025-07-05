#!/usr/bin/env python3
"""
CPOR Protocol - Task 2: Cryptography Helpers Validation Script

This script validates the cryptography helpers, Ed25519 signing/verification,
TPM stub, and key management logic for the CPOR protocol.
"""

import sys
import traceback

try:
    print("\U0001f504 Testing cryptography helpers imports...")
    from cpor.crypto import (
        CryptoManager, quick_generate_keypair, quick_verify
    )
    import nacl.signing
    print("\u2705 All crypto imports successful")

    # Test Ed25519 key generation
    print("\n\U0001f504 Testing Ed25519 key generation...")
    keypair = quick_generate_keypair("test_key", storage_type="software")
    priv = keypair.private_key
    pub = keypair.public_key
    assert isinstance(priv, nacl.signing.SigningKey)
    assert isinstance(pub, nacl.signing.VerifyKey)
    print("\u2705 Ed25519 keypair generated")

    # Test signing and verification
    print("\n\U0001f504 Testing Ed25519 signing and verification...")
    message = b"test message for signing"
    signature = priv.sign(message).signature
    assert isinstance(signature, bytes)
    assert len(signature) == 64
    assert quick_verify(pub, message, signature)
    print("\u2705 Ed25519 sign/verify successful")

    # Test CryptoManager software key management
    print("\n\U0001f504 Testing CryptoManager software key management...")
    cm = CryptoManager()
    keypair2 = cm.generate_keypair("test_key2", storage_type="software")
    key_id2 = keypair2.key_id
    assert key_id2 in cm.list_keys()
    msg = b"CPOR test message"
    sig = cm.sign_data(key_id2, msg)
    assert cm.verify_signature(keypair2.public_key, msg, sig)
    print("\u2705 CryptoManager software key sign/verify successful")

    # Test TPM stub interface
    print("\n\U0001f504 Testing TPM stub interface...")
    # Accessing _tpm is intentional for validation script; in production use public API only
    tpm = cm._tpm  # type: ignore[attr-defined]
    if tpm.is_available():
        tpm_keypair = cm.generate_keypair("test_tpm_key", storage_type="tpm")
        tpm_key_id = tpm_keypair.key_id
        assert tpm_key_id in cm.list_keys()
        tpm_sig = cm.sign_data(tpm_key_id, msg)
        assert cm.verify_signature(tpm_keypair.public_key, msg, tpm_sig)
        print("\u2705 TPM stub sign/verify successful")
    else:
        print("\u26a0\ufe0f TPM stub not available; skipping TPM tests.")

    print("\n\U0001f389 All cryptography helper tests passed!\n")
    sys.exit(0)

except Exception as e:
    print("\n\u274c Cryptography helper validation failed:")
    traceback.print_exc()
    sys.exit(1)

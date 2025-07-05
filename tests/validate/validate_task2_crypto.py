#!/usr/bin/env python3
"""
CPOR Protocol - Task 2: Cryptography Helpers Validation Script

This script validates the cryptography helpers, Ed25519 signing/verification,
TPM stub, and key management logic for the CPOR protocol.
"""

import sys
import traceback
from typing import Any

try:
    print("🔄 Testing cryptography helpers imports...")
    from cpor.crypto import (
        CryptoManager, TPMInterface, generate_ed25519_keypair, sign_message, verify_signature, generate_nonce
    )
    import nacl.signing
    print("✅ All crypto imports successful")

    # Test Ed25519 key generation
    print("\n🔄 Testing Ed25519 key generation...")
    priv, pub = generate_ed25519_keypair()
    assert isinstance(priv, nacl.signing.SigningKey)
    assert isinstance(pub, nacl.signing.VerifyKey)
    print("✅ Ed25519 keypair generated")

    # Test signing and verification
    print("\n🔄 Testing Ed25519 signing and verification...")
    message = b"test message for signing"
    signature = sign_message(priv, message)
    assert isinstance(signature, bytes)
    assert len(signature) == 64
    assert verify_signature(pub, message, signature)
    print("✅ Ed25519 sign/verify successful")

    # Test CryptoManager software key management
    print("\n🔄 Testing CryptoManager software key management...")
    cm = CryptoManager()
    key_id = cm.generate_keypair(storage_type="software")
    assert key_id in cm.list_keys()
    msg = b"CPOR test message"
    sig = cm.sign(key_id, msg)
    assert cm.verify(key_id, msg, sig)
    print("✅ CryptoManager software key sign/verify successful")

    # Test TPM stub interface
    print("\n🔄 Testing TPM stub interface...")
    tpm = cm.tpm
    if tpm.is_available():
        tpm_key_id = cm.generate_keypair(storage_type="tpm")
        assert tpm_key_id in cm.list_keys()
        tpm_sig = cm.sign(tpm_key_id, msg)
        assert cm.verify(tpm_key_id, msg, tpm_sig)
        print("✅ TPM stub sign/verify successful")
    else:
        print("ℹ️ TPM not available (stub mode), skipping TPM tests.")

    # Test nonce generation
    print("\n🔄 Testing nonce generation...")
    nonce = generate_nonce(16)
    assert isinstance(nonce, bytes)
    assert len(nonce) == 16
    print("✅ Nonce generated: ", nonce.hex())

    print("\n🎉 ALL CRYPTO VALIDATION TESTS PASSED!")

except Exception as e:
    print(f"\n❌ Crypto validation failed with error: {e}")
    print(f"Error type: {type(e).__name__}")
    print("Traceback:")
    traceback.print_exc()
    sys.exit(1)

"""Unit tests for CPOR protocol cryptography helpers."""

import pytest
import nacl.signing

from cpor.crypto import (
    CryptoManager,
    KeyPair,
    TPMStub,
    generate_nonce,
    generate_session_key,
    constant_time_compare,
    derive_key_id,
    validate_ed25519_key,
    quick_generate_keypair,
    quick_sign,
    quick_verify,
    get_crypto_manager,
    set_crypto_manager,
    # Exceptions
    CPORCryptoError,
    KeyGenerationError,
    SigningError,
    VerificationError,
    TPMError,
    KeyStorageError,
)


class TestKeyPair:
    """Test KeyPair functionality."""
    
    def test_valid_software_keypair(self) -> None:
        """Test creating a valid software KeyPair."""
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key
        
        keypair = KeyPair(
            private_key=signing_key,
            public_key=verify_key,
            key_id="test_key",
            storage_type="software"
        )
        
        assert keypair.key_id == "test_key"
        assert keypair.storage_type == "software"
        assert len(keypair.public_key_bytes) == 32
        assert len(keypair.private_key_bytes) == 32
    
    def test_valid_tpm_keypair(self) -> None:
        """Test creating a valid TPM KeyPair."""
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key
        
        keypair = KeyPair(
            private_key=signing_key,
            public_key=verify_key,
            key_id="tpm_key",
            storage_type="tpm"
        )
        
        assert keypair.key_id == "tpm_key"
        assert keypair.storage_type == "tpm"
        assert len(keypair.public_key_bytes) == 32
        
        # TPM keys should not allow private key export
        with pytest.raises(KeyStorageError, match="Cannot export private key from TPM"):
            _ = keypair.private_key_bytes
    
    def test_invalid_storage_type(self) -> None:
        """Test that invalid storage type is rejected."""
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key
        
        with pytest.raises(KeyGenerationError, match="storage_type must be"):
            KeyPair(
                private_key=signing_key,
                public_key=verify_key,
                key_id="test_key",
                storage_type="invalid"
            )


class TestTPMStub:
    """Test TPM stub functionality."""
    
    def test_tpm_availability(self) -> None:
        """Test TPM availability checking."""
        tpm = TPMStub()
        assert tpm.is_available() is True
        
        tpm.set_available(False)
        assert tpm.is_available() is False
        
        tpm.set_available(True)
        assert tpm.is_available() is True
    
    def test_key_generation(self) -> None:
        """Test TPM key generation."""
        tpm = TPMStub()
        
        public_key = tpm.generate_key("test_key")
        assert len(public_key) == 32
        
        # Should be able to retrieve the same key
        retrieved_key = tpm.get_public_key("test_key")
        assert public_key == retrieved_key
    
    def test_duplicate_key_generation(self) -> None:
        """Test that duplicate key generation fails."""
        tpm = TPMStub()
        
        tpm.generate_key("test_key")
        
        with pytest.raises(TPMError, match="already exists"):
            tpm.generate_key("test_key")
    
    def test_signing_operations(self) -> None:
        """Test TPM signing operations."""
        tpm = TPMStub()
        
        tpm.generate_key("sign_key")
        
        test_data = b"Hello, TPM!"
        signature = tpm.sign("sign_key", test_data)
        
        assert len(signature) == 64
        
        # Verify signature using public key
        public_key = tpm.get_public_key("sign_key")
        verify_key = nacl.signing.VerifyKey(public_key)
        
        # This should not raise an exception
        verify_key.verify(test_data, signature)
    
    def test_nonexistent_key_operations(self) -> None:
        """Test operations on nonexistent keys."""
        tpm = TPMStub()
        
        with pytest.raises(TPMError, match="not found"):
            tpm.get_public_key("nonexistent")
        
        with pytest.raises(TPMError, match="not found"):
            tpm.sign("nonexistent", b"data")
    
    def test_key_deletion(self) -> None:
        """Test key deletion."""
        tpm = TPMStub()
        
        tpm.generate_key("delete_me")
        assert tpm.delete_key("delete_me") is True
        assert tpm.delete_key("nonexistent") is False
        
        # Should not be able to access deleted key
        with pytest.raises(TPMError, match="not found"):
            tpm.get_public_key("delete_me")


class TestCryptoManager:
    """Test main CryptoManager functionality."""
    
    def test_initialization(self) -> None:
        """Test CryptoManager initialization."""
        crypto = CryptoManager()
        assert crypto.tpm_available is True  # Using stub by default
        
        # Test with custom TPM
        custom_tpm = TPMStub()
        custom_tpm.set_available(False)
        crypto_custom = CryptoManager(custom_tpm)
        assert crypto_custom.tpm_available is False
    
    def test_software_keypair_generation(self) -> None:
        """Test software key pair generation."""
        crypto = CryptoManager()
        
        keypair = crypto.generate_keypair("sw_key", "software")
        
        assert keypair.key_id == "sw_key"
        assert keypair.storage_type == "software"
        assert len(keypair.public_key_bytes) == 32
        
        # Should be able to retrieve the key
        retrieved = crypto.get_keypair("sw_key")
        assert retrieved is not None
        assert retrieved.key_id == "sw_key"
    
    def test_tpm_keypair_generation(self) -> None:
        """Test TPM key pair generation."""
        crypto = CryptoManager()
        
        keypair = crypto.generate_keypair("tpm_key", "tpm")
        
        assert keypair.key_id == "tpm_key"
        assert keypair.storage_type == "tpm"
        assert len(keypair.public_key_bytes) == 32
    
    def test_tpm_fallback(self) -> None:
        """Test fallback to software when TPM unavailable."""
        tpm = TPMStub()
        tpm.set_available(False)
        crypto = CryptoManager(tpm)
        
        # Should fall back to software storage
        keypair = crypto.generate_keypair("fallback_key", "tpm")
        assert keypair.storage_type == "software"
    
    def test_signing_operations(self) -> None:
        """Test signing and verification."""
        crypto = CryptoManager()
        
        # Test software signing
        keypair = crypto.generate_keypair("sign_key", "software")
        test_data = b"Sign this message"
        
        signature = crypto.sign_data("sign_key", test_data)
        assert len(signature) == 64
        
        # Verify with manager
        is_valid = crypto.verify_signature(keypair.public_key_bytes, test_data, signature)
        assert is_valid is True
        
        # Verify with wrong data should fail
        is_invalid = crypto.verify_signature(keypair.public_key_bytes, b"wrong data", signature)
        assert is_invalid is False
    
    def test_verification_with_verify_key_object(self) -> None:
        """Test verification using VerifyKey object."""
        crypto = CryptoManager()
        
        keypair = crypto.generate_keypair("verify_key", "software")
        test_data = b"Verify this"
        
        signature = crypto.sign_data("verify_key", test_data)
        
        # Test with VerifyKey object
        is_valid = crypto.verify_signature(keypair.public_key, test_data, signature)
        assert is_valid is True
    
    def test_key_deletion(self) -> None:
        """Test key deletion."""
        crypto = CryptoManager()
        
        crypto.generate_keypair("delete_me", "software")
        assert crypto.get_keypair("delete_me") is not None
        
        deleted = crypto.delete_key("delete_me")
        assert deleted is True
        assert crypto.get_keypair("delete_me") is None
        
        # Deleting nonexistent key should return False
        deleted_again = crypto.delete_key("delete_me")
        assert deleted_again is False
    
    def test_list_keys(self) -> None:
        """Test key listing."""
        crypto = CryptoManager()
        
        initial_keys = crypto.list_keys()
        
        crypto.generate_keypair("list_key1", "software")
        crypto.generate_keypair("list_key2", "software")
        
        keys = crypto.list_keys()
        assert "list_key1" in keys
        assert "list_key2" in keys
        assert len(keys) == len(initial_keys) + 2
    
    def test_invalid_operations(self) -> None:
        """Test error conditions."""
        crypto = CryptoManager()
        
        # Test signing with nonexistent key
        with pytest.raises(KeyStorageError, match="not found"):
            crypto.sign_data("nonexistent", b"data")
        
        # Test invalid storage type
        with pytest.raises(KeyGenerationError, match="storage_type must be"):
            crypto.generate_keypair("invalid", "invalid_type")
        
        # Test verification with invalid public key
        with pytest.raises(VerificationError, match="must be 32 bytes"):
            crypto.verify_signature(b"short", b"data", b"x" * 64)
        
        # Test verification with invalid signature
        keypair = crypto.generate_keypair("test_invalid", "software")
        with pytest.raises(VerificationError, match="must be 64 bytes"):
            crypto.verify_signature(keypair.public_key_bytes, b"data", b"short")


class TestUtilityFunctions:
    """Test utility crypto functions."""
    
    def test_nonce_generation(self) -> None:
        """Test nonce generation."""
        nonce1 = generate_nonce(16)
        nonce2 = generate_nonce(16)
        
        assert len(nonce1) == 16
        assert len(nonce2) == 16
        assert nonce1 != nonce2  # Should be different
        
        # Test different sizes
        assert len(generate_nonce(32)) == 32
        assert len(generate_nonce(1)) == 1
        
        # Test invalid sizes
        with pytest.raises(ValueError, match="must be between 1 and 1024"):
            generate_nonce(0)
        
        with pytest.raises(ValueError, match="must be between 1 and 1024"):
            generate_nonce(2000)
    
    def test_session_key_generation(self) -> None:
        """Test session key generation."""
        key1 = generate_session_key()
        key2 = generate_session_key()
        
        assert len(key1) == 32
        assert len(key2) == 32
        assert key1 != key2
    
    def test_constant_time_compare(self) -> None:
        """Test constant-time comparison."""
        data1 = b"same_data"
        data2 = b"same_data"
        data3 = b"different"
        
        assert constant_time_compare(data1, data2) is True
        assert constant_time_compare(data1, data3) is False
        assert constant_time_compare(b"", b"") is True
    
    def test_key_id_derivation(self) -> None:
        """Test key ID derivation."""
        public_key = b"\x01" * 32
        
        key_id1 = derive_key_id(public_key)
        key_id2 = derive_key_id(public_key, "custom")
        
        assert key_id1.startswith("cpor_")
        assert key_id2.startswith("custom_")
        assert len(key_id1.split("_")[1]) == 16  # 8 bytes as hex
        
        # Same public key should give same ID
        key_id3 = derive_key_id(public_key)
        assert key_id1 == key_id3
        
        # Invalid public key
        with pytest.raises(ValueError, match="must be 32 bytes"):
            derive_key_id(b"short")
    
    def test_ed25519_key_validation(self) -> None:
        """Test Ed25519 key validation."""
        # Valid keys
        signing_key = nacl.signing.SigningKey.generate()
        public_key_bytes = bytes(signing_key.verify_key)
        private_key_bytes = bytes(signing_key)
        
        assert validate_ed25519_key(public_key_bytes, "public") is True
        assert validate_ed25519_key(private_key_bytes, "private") is True
        
        # Invalid keys
        assert validate_ed25519_key(b"short", "public") is False
        assert validate_ed25519_key(b"short", "private") is False
        assert validate_ed25519_key(b"x" * 32, "public") is False  # Invalid key data
        
        # Invalid key type
        with pytest.raises(ValueError, match="must be 'public' or 'private'"):
            validate_ed25519_key(public_key_bytes, "invalid")


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_quick_operations(self) -> None:
        """Test quick crypto operations."""
        # Generate keypair
        keypair = quick_generate_keypair("quick_key", "software")
        assert keypair.key_id == "quick_key"
        
        # Sign data
        test_data = b"Quick test data"
        signature = quick_sign("quick_key", test_data)
        assert len(signature) == 64
        
        # Verify signature
        is_valid = quick_verify(keypair.public_key_bytes, test_data, signature)
        assert is_valid is True
    
    def test_crypto_manager_singleton(self) -> None:
        """Test default crypto manager handling."""
        # Get default manager
        manager1 = get_crypto_manager()
        manager2 = get_crypto_manager()
        assert manager1 is manager2  # Should be same instance
        
        # Set custom manager
        custom_manager = CryptoManager()
        set_crypto_manager(custom_manager)
        
        manager3 = get_crypto_manager()
        assert manager3 is custom_manager
        assert manager3 is not manager1


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_all_exception_types(self) -> None:
        """Test that all custom exceptions can be raised."""
        with pytest.raises(CPORCryptoError):
            raise CPORCryptoError("Base crypto error")
        
        with pytest.raises(KeyGenerationError):
            raise KeyGenerationError("Key generation failed")
        
        with pytest.raises(SigningError):
            raise SigningError("Signing failed")
        
        with pytest.raises(VerificationError):
            raise VerificationError("Verification failed")
        
        with pytest.raises(TPMError):
            raise TPMError("TPM operation failed")
        
        with pytest.raises(KeyStorageError):
            raise KeyStorageError("Key storage failed")
    
    def test_exception_inheritance(self) -> None:
        """Test that specific exceptions inherit from base."""
        assert issubclass(KeyGenerationError, CPORCryptoError)
        assert issubclass(SigningError, CPORCryptoError)
        assert issubclass(VerificationError, CPORCryptoError)
        assert issubclass(TPMError, CPORCryptoError)
        assert issubclass(KeyStorageError, CPORCryptoError)

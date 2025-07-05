"""
CPOR Protocol Cryptography Helpers

This module provides Ed25519 cryptographic operations, key management, and TPM integration
for the CPOR protocol. It includes key generation, signing/verification, nonce generation,
and a pluggable TPM interface.

Protocol Version: CPOR-2
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Optional, Union, Protocol, runtime_checkable

import nacl.signing
from nacl.exceptions import BadSignatureError

logger = logging.getLogger(__name__)


class CPORCryptoError(Exception):
    """Base exception for CPOR cryptography errors."""
    pass


class KeyGenerationError(CPORCryptoError):
    """Raised when key generation fails."""
    pass


class SigningError(CPORCryptoError):
    """Raised when message signing fails."""
    pass


class VerificationError(CPORCryptoError):
    """Raised when signature verification fails."""
    pass


class TPMError(CPORCryptoError):
    """Raised when TPM operations fail."""
    pass


class KeyStorageError(CPORCryptoError):
    """Raised when key storage operations fail."""
    pass


@runtime_checkable
class TPMInterface(Protocol):
    """Protocol defining TPM interface for key operations."""
    
    def is_available(self) -> bool:
        """Check if TPM is available and functional."""
        ...
    
    def generate_key(self, key_id: str) -> bytes:
        """Generate a new Ed25519 key in TPM and return public key."""
        ...
    
    def sign(self, key_id: str, data: bytes) -> bytes:
        """Sign data using TPM-stored private key."""
        ...
    
    def get_public_key(self, key_id: str) -> bytes:
        """Retrieve public key for a stored private key."""
        ...
    
    def delete_key(self, key_id: str) -> bool:
        """Delete a key from TPM storage."""
        ...


@dataclass(frozen=True)
class KeyPair:
    """Ed25519 key pair container."""
    
    private_key: nacl.signing.SigningKey
    public_key: nacl.signing.VerifyKey
    key_id: str
    storage_type: str  # "software" or "tpm"
    
    def __post_init__(self) -> None:
        """Validate key pair."""
        if self.storage_type not in ["software", "tpm"]:
            raise KeyGenerationError("storage_type must be 'software' or 'tpm'")
    
    @property
    def public_key_bytes(self) -> bytes:
        """Return public key as 32-byte Ed25519 public key."""
        return bytes(self.public_key)
    
    @property
    def private_key_bytes(self) -> bytes:
        """Return private key as 32-byte Ed25519 private key (software only)."""
        if self.storage_type == "tpm":
            raise KeyStorageError("Cannot export private key from TPM storage")
        return bytes(self.private_key)


class TPMStub:
    """Stub implementation of TPM interface for development/testing."""
    
    def __init__(self) -> None:
        """Initialize TPM stub."""
        self._keys: dict[str, nacl.signing.SigningKey] = {}
        self._available = True
        logger.info("TPM stub initialized")
    
    def is_available(self) -> bool:
        """Check if TPM stub is available."""
        return self._available
    
    def generate_key(self, key_id: str) -> bytes:
        """Generate a new Ed25519 key in stub storage."""
        if key_id in self._keys:
            raise TPMError(f"Key {key_id} already exists in TPM")
        
        try:
            signing_key = nacl.signing.SigningKey.generate()
            self._keys[key_id] = signing_key
            public_key = bytes(signing_key.verify_key)
            
            logger.info(f"Generated TPM key: {key_id}")
            return public_key
        
        except Exception as e:
            raise TPMError(f"Failed to generate TPM key {key_id}: {e}")
    
    def sign(self, key_id: str, data: bytes) -> bytes:
        """Sign data using TPM-stored private key."""
        if key_id not in self._keys:
            raise TPMError(f"Key {key_id} not found in TPM")
        
        try:
            signing_key = self._keys[key_id]
            signature = signing_key.sign(data)
            return signature.signature
        
        except Exception as e:
            raise TPMError(f"Failed to sign with TPM key {key_id}: {e}")
    
    def get_public_key(self, key_id: str) -> bytes:
        """Retrieve public key for a stored private key."""
        if key_id not in self._keys:
            raise TPMError(f"Key {key_id} not found in TPM")
        
        signing_key = self._keys[key_id]
        return bytes(signing_key.verify_key)
    
    def delete_key(self, key_id: str) -> bool:
        """Delete a key from TPM storage."""
        if key_id in self._keys:
            del self._keys[key_id]
            logger.info(f"Deleted TPM key: {key_id}")
            return True
        return False
    
    def set_available(self, available: bool) -> None:
        """Set TPM availability for testing."""
        self._available = available
        logger.info(f"TPM stub availability set to: {available}")


class CryptoManager:
    """Main cryptography manager for CPOR protocol operations."""
    
    def __init__(self, tpm_interface: Optional[TPMInterface] = None) -> None:
        """
        Initialize crypto manager.
        
        Args:
            tpm_interface: TPM interface implementation. If None, uses stub.
        """
        self._tpm = tpm_interface or TPMStub()
        self._software_keys: dict[str, KeyPair] = {}
        
        logger.info(f"CryptoManager initialized with TPM available: {self._tpm.is_available()}")
    
    @property
    def tpm_available(self) -> bool:
        """Check if TPM is available for key operations."""
        return self._tpm.is_available()
    
    def generate_keypair(self, key_id: str, storage_type: str = "software") -> KeyPair:
        """
        Generate a new Ed25519 key pair.
        
        Args:
            key_id: Unique identifier for the key
            storage_type: "software" or "tpm"
            
        Returns:
            KeyPair object
            
        Raises:
            KeyGenerationError: If key generation fails
            TPMError: If TPM operations fail
        """
        if storage_type not in ["software", "tpm"]:
            raise KeyGenerationError("storage_type must be 'software' or 'tpm'")
        
        if storage_type == "tpm":
            if not self._tpm.is_available():
                logger.warning("TPM not available, falling back to software storage")
                storage_type = "software"
            else:
                return self._generate_tpm_keypair(key_id)
        
        return self._generate_software_keypair(key_id)
    
    def _generate_software_keypair(self, key_id: str) -> KeyPair:
        """Generate software-stored Ed25519 key pair."""
        try:
            signing_key = nacl.signing.SigningKey.generate()
            verify_key = signing_key.verify_key
            
            keypair = KeyPair(
                private_key=signing_key,
                public_key=verify_key,
                key_id=key_id,
                storage_type="software"
            )
            
            self._software_keys[key_id] = keypair
            logger.info(f"Generated software key pair: {key_id}")
            return keypair
            
        except Exception as e:
            raise KeyGenerationError(f"Failed to generate software key pair {key_id}: {e}")
    
    def _generate_tpm_keypair(self, key_id: str) -> KeyPair:
        """Generate TPM-stored Ed25519 key pair."""
        try:
            public_key_bytes = self._tpm.generate_key(key_id)
            verify_key = nacl.signing.VerifyKey(public_key_bytes)
            
            # Create a dummy signing key for the KeyPair interface
            # The actual signing will be done through TPM
            dummy_signing_key = nacl.signing.SigningKey(b"\x00" * 32)
            
            keypair = KeyPair(
                private_key=dummy_signing_key,
                public_key=verify_key,
                key_id=key_id,
                storage_type="tpm"
            )
            
            logger.info(f"Generated TPM key pair: {key_id}")
            return keypair
            
        except Exception as e:
            raise KeyGenerationError(f"Failed to generate TPM key pair {key_id}: {e}")
    
    def get_keypair(self, key_id: str) -> Optional[KeyPair]:
        """
        Retrieve a key pair by ID.
        
        Args:
            key_id: Key identifier
            
        Returns:
            KeyPair if found, None otherwise
        """
        # Check software keys first
        if key_id in self._software_keys:
            return self._software_keys[key_id]
        
        # Check TPM keys
        try:
            if self._tpm.is_available():
                public_key_bytes = self._tpm.get_public_key(key_id)
                verify_key = nacl.signing.VerifyKey(public_key_bytes)
                
                dummy_signing_key = nacl.signing.SigningKey(b"\x00" * 32)
                return KeyPair(
                    private_key=dummy_signing_key,
                    public_key=verify_key,
                    key_id=key_id,
                    storage_type="tpm"
                )
        except TPMError:
            # Key not found in TPM
            pass
        
        return None
    
    def sign_data(self, key_id: str, data: bytes) -> bytes:
        """
        Sign data using the specified key.
        
        Args:
            key_id: Key identifier
            data: Data to sign
            
        Returns:
            64-byte Ed25519 signature
            
        Raises:
            SigningError: If signing fails
            KeyStorageError: If key not found
        """
        # Check software keys
        if key_id in self._software_keys:
            keypair = self._software_keys[key_id]
            try:
                signature = keypair.private_key.sign(data)
                return signature.signature
            except Exception as e:
                raise SigningError(f"Failed to sign with software key {key_id}: {e}")
        
        # Check TPM keys
        try:
            if self._tpm.is_available():
                return self._tpm.sign(key_id, data)
        except TPMError as e:
            # If the TPMError is due to missing key, raise KeyStorageError
            if "not found" in str(e):
                raise KeyStorageError(f"Key {key_id} not found in any storage")
            raise SigningError(f"Failed to sign with TPM key {key_id}: {e}")
        
        raise KeyStorageError(f"Key {key_id} not found in any storage")
    
    def verify_signature(self, public_key: Union[bytes, nacl.signing.VerifyKey], 
                        data: bytes, signature: bytes) -> bool:
        """
        Verify Ed25519 signature.
        
        Args:
            public_key: 32-byte public key or VerifyKey object
            data: Original data that was signed
            signature: 64-byte signature to verify
            
        Returns:
            True if signature is valid, False otherwise
            
        Raises:
            VerificationError: If verification operation fails
        """
        try:
            # Type narrowing with explicit conversion
            if isinstance(public_key, bytes):
                if len(public_key) != 32:
                    raise VerificationError("Public key must be 32 bytes")
                verify_key = nacl.signing.VerifyKey(public_key)
            elif isinstance(public_key, (bytearray, memoryview)):
                # Handle bytes-like objects
                key_bytes = bytes(public_key)
                if len(key_bytes) != 32:
                    raise VerificationError("Public key must be 32 bytes")
                verify_key = nacl.signing.VerifyKey(key_bytes)
            else:
                # Must be VerifyKey at this point
                verify_key = public_key
            
            if len(signature) != 64:
                raise VerificationError("Signature must be 64 bytes")
            
            # Now verify_key is definitely a VerifyKey object
            verify_key.verify(data, signature)
            return True
            
        except BadSignatureError:
            return False
        except Exception as e:
            raise VerificationError(f"Signature verification failed: {e}")
    
    def delete_key(self, key_id: str) -> bool:
        """
        Delete a key from storage.
        
        Args:
            key_id: Key identifier
            
        Returns:
            True if key was deleted, False if not found
        """
        deleted = False
        
        # Delete from software storage
        if key_id in self._software_keys:
            del self._software_keys[key_id]
            deleted = True
            logger.info(f"Deleted software key: {key_id}")
        
        # Delete from TPM storage
        try:
            if self._tpm.is_available():
                if self._tpm.delete_key(key_id):
                    deleted = True
        except TPMError:
            pass  # Key not in TPM
        
        return deleted
    
    def list_keys(self) -> list[str]:
        """
        List all available key IDs.
        
        Returns:
            List of key identifiers
        """
        keys = list(self._software_keys.keys())
        
        # Note: TPM stub doesn't provide key listing in this implementation
        # Real TPM implementations would enumerate keys here
        
        return keys


# Utility functions for common crypto operations

def generate_nonce(size: int = 16) -> bytes:
    """
    Generate cryptographically secure random nonce.
    
    Args:
        size: Number of bytes to generate (default: 16)
        
    Returns:
        Random bytes
        
    Raises:
        ValueError: If size is invalid
    """
    if size < 1 or size > 1024:
        raise ValueError("Nonce size must be between 1 and 1024 bytes")
    
    try:
        return secrets.token_bytes(size)
    except Exception as e:
        raise CPORCryptoError(f"Failed to generate nonce: {e}")


def generate_session_key() -> bytes:
    """
    Generate a 32-byte session key for symmetric encryption.
    
    Returns:
        32-byte random key
    """
    return generate_nonce(32)


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """
    Constant-time comparison of byte strings.
    
    Args:
        a: First byte string
        b: Second byte string
        
    Returns:
        True if equal, False otherwise
    """
    return secrets.compare_digest(a, b)


def derive_key_id(public_key: bytes, prefix: str = "cpor") -> str:
    """
    Derive a consistent key ID from a public key.
    
    Args:
        public_key: 32-byte Ed25519 public key
        prefix: Prefix for the key ID
        
    Returns:
        String key identifier
    """
    if len(public_key) != 32:
        raise ValueError("Public key must be 32 bytes")
    
    # Use first 8 bytes of public key as hex string
    key_suffix = public_key[:8].hex()
    return f"{prefix}_{key_suffix}"


def validate_ed25519_key(key_bytes: bytes, key_type: str = "public") -> bool:
    """
    Validate Ed25519 key format.
    
    Args:
        key_bytes: Key bytes to validate
        key_type: "public" or "private"
        
    Returns:
        True if valid, False otherwise
    """
    if key_type == "public":
        if len(key_bytes) != 32:
            return False
        try:
            nacl.signing.VerifyKey(key_bytes)
            return True
        except Exception:
            return False
    
    elif key_type == "private":
        if len(key_bytes) != 32:
            return False
        try:
            nacl.signing.SigningKey(key_bytes)
            return True
        except Exception:
            return False
    
    else:
        raise ValueError("key_type must be 'public' or 'private'")


# Default crypto manager instance
_default_crypto_manager: Optional[CryptoManager] = None


def get_crypto_manager() -> CryptoManager:
    """
    Get the default crypto manager instance.
    
    Returns:
        CryptoManager instance
    """
    global _default_crypto_manager
    if _default_crypto_manager is None:
        _default_crypto_manager = CryptoManager()
    return _default_crypto_manager


def set_crypto_manager(manager: CryptoManager) -> None:
    """
    Set the default crypto manager instance.
    
    Args:
        manager: CryptoManager instance to use as default
    """
    global _default_crypto_manager
    _default_crypto_manager = manager


# Convenience functions using default manager

def quick_generate_keypair(key_id: str, storage_type: str = "software") -> KeyPair:
    """Generate key pair using default crypto manager."""
    return get_crypto_manager().generate_keypair(key_id, storage_type)


def quick_sign(key_id: str, data: bytes) -> bytes:
    """Sign data using default crypto manager."""
    return get_crypto_manager().sign_data(key_id, data)


def quick_verify(public_key: Union[bytes, nacl.signing.VerifyKey], 
                data: bytes, signature: bytes) -> bool:
    """Verify signature using default crypto manager."""
    return get_crypto_manager().verify_signature(public_key, data, signature)


# Example usage and test vectors
if __name__ == "__main__":
    # Example usage
    crypto = CryptoManager()
    
    # Generate a key pair
    keypair = crypto.generate_keypair("test_key", "software")
    print(f"Generated key: {keypair.key_id}")
    print(f"Public key: {keypair.public_key_bytes.hex()}")
    
    # Sign some data
    test_data = b"Hello, CPOR!"
    signature = crypto.sign_data("test_key", test_data)
    print(f"Signature: {signature.hex()}")
    
    # Verify signature
    is_valid = crypto.verify_signature(keypair.public_key_bytes, test_data, signature)
    print(f"Signature valid: {is_valid}")
    
    # Generate nonce
    nonce = generate_nonce(16)
    print(f"Nonce: {nonce.hex()}")

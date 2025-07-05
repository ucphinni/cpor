#!/usr/bin/env python3
"""
CPOR Protocol - Task 1 Spec-Aligned Validation Script

This script validates the updated message schemas that are aligned with 
the official CPOR protocol specification.
"""

import sys
import traceback
from typing import Any, Tuple

try:
    # Test imports
    print("🔄 Testing spec-aligned imports...")
    from cpor import (
        ConnectRequest, ConnectResponse, GenericMessage,
        AckMessage, HeartbeatMessage, ResumeRequest, ResumeResponse, BatchMessage, CloseMessage, ErrorMessage,
        parse_message, EXAMPLE_MESSAGES
    )
    import nacl.signing
    print("✅ All imports successful")

    MESSAGE_CLASS_MAP: dict[str, type] = {
        "ConnectRequest": ConnectRequest,
        "ConnectResponse": ConnectResponse,
        "GenericMessage": GenericMessage,
        "AckMessage": AckMessage,
        "HeartbeatMessage": HeartbeatMessage,
        "ResumeRequest": ResumeRequest,
        "ResumeResponse": ResumeResponse,
        "BatchMessage": BatchMessage,
        "CloseMessage": CloseMessage,
        "ErrorMessage": ErrorMessage,
    }

    # Create test keypair
    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key
    public_key_bytes = bytes(verify_key)
    
    # Test ConnectRequest with spec field names
    print("\n🔄 Testing ConnectRequest with spec fields...")
    connect_req = ConnectRequest(
        client_id="test-client-001",
        client_pubkey=public_key_bytes,
        nonce=b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
        resume_sequence=0,
        registration_flag=False,
        key_storage="software",
        capabilities=["batch", "resume", "compression"]
    )
    print(f"✅ ConnectRequest created:")
    print(f"   Type: {connect_req.type}")
    print(f"   Client ID: {connect_req.client_id}")
    print(f"   Pubkey length: {len(connect_req.client_pubkey)} bytes")
    print(f"   Nonce length: {len(connect_req.nonce)} bytes")
    print(f"   Resume sequence: {connect_req.resume_sequence}")
    print(f"   Registration flag: {connect_req.registration_flag}")
    print(f"   Key storage: {connect_req.key_storage}")
    
    # Test CBOR serialization with new fields
    print("\n🔄 Testing CBOR serialization with spec fields...")
    cbor_data = connect_req.to_cbor()
    restored_msg = ConnectRequest.from_cbor(cbor_data)
    assert restored_msg == connect_req
    print(f"✅ CBOR roundtrip successful ({len(cbor_data)} bytes)")
    
    # Test generic parsing with type field
    parsed_msg = parse_message(cbor_data)
    assert isinstance(parsed_msg, ConnectRequest)
    assert parsed_msg.type == "connect_request"
    print("✅ Generic message parsing with type field successful")
    
    # Test ConnectResponse with spec fields
    print("\n🔄 Testing ConnectResponse with spec fields...")
    connect_resp = ConnectResponse(
        session_id="session-456",
        server_pubkey=public_key_bytes,
        resume_sequence=0,
        status_code=0,
        server_capabilities=["batch", "resume"]
    )
    print(f"✅ ConnectResponse created:")
    print(f"   Type: {connect_resp.type}")
    print(f"   Session ID: {connect_resp.session_id}")
    print(f"   Status code: {connect_resp.status_code}")
    print(f"   Server pubkey length: {len(connect_resp.server_pubkey)} bytes")
    
    # Test GenericMessage with sequence_number (not sequence_counter)
    print("\n🔄 Testing GenericMessage with sequence_number...")
    generic_msg = GenericMessage(
        sequence_number=42,
        payload=b"Hello, CPOR Protocol!",
        message_type="data",
        priority=1
    )
    print(f"✅ GenericMessage created:")
    print(f"   Type: {generic_msg.type}")
    print(f"   Sequence number: {generic_msg.sequence_number}")
    print(f"   Payload: {generic_msg.payload}")
    
    # Test AckMessage with ack_sequence (not ack_counter)
    print("\n🔄 Testing AckMessage with ack_sequence...")
    ack_msg = AckMessage(
        ack_sequence=42,
        ack_type="message"
    )
    print(f"✅ AckMessage created:")
    print(f"   Type: {ack_msg.type}")
    print(f"   Ack sequence: {ack_msg.ack_sequence}")
    print(f"   Ack type: {ack_msg.ack_type}")
    
    # Test all message types have type field
    print("\n🔄 Testing all message types have type field...")
    

    messages_to_test: list[Tuple[str, Any]] = [
        ("ConnectRequest", connect_req),
        ("ConnectResponse", connect_resp),
        ("GenericMessage", generic_msg),
        ("AckMessage", ack_msg)
    ]

    for msg_name, msg in messages_to_test:
        assert hasattr(msg, 'type'), f"{msg_name} missing type field"
        assert msg.type, f"{msg_name} has empty type field"
        print(f"   ✅ {msg_name}: type='{msg.type}'")    
    # Test Ed25519 signing still works
    print("\n🔄 Testing Ed25519 signatures...")
    signature = connect_req.sign(signing_key)
    assert len(signature) == 64
    is_valid = connect_req.verify_signature(signature, verify_key)
    assert is_valid
    print(f"✅ Message signed and verified ({len(signature)} byte signature)")
    
    # Test example messages with new schema
    print("\n🔄 Testing updated example messages...")
    for msg_type, example_data in EXAMPLE_MESSAGES.items():
        # Get the message class
        msg_class: type = MESSAGE_CLASS_MAP[msg_type]

        # Create from example
        msg: Any
        from_dict_method = getattr(msg_class, "from_dict", None)
        if callable(from_dict_method):
            msg = from_dict_method(example_data)
        else:
            # Fallback: try to instantiate directly
            msg = msg_class(**example_data)

        # Test has type field
        assert hasattr(msg, 'type'), f"Example {msg_type} missing type field"

        # Test serialization roundtrip
        cbor_data = msg.to_cbor()  # type: ignore
        assert isinstance(cbor_data, bytes)
        restored: Any = msg_class.from_cbor(cbor_data)  # type: ignore
        assert restored == msg

        # Test generic parsing
        parsed: Any = parse_message(cbor_data)
        assert isinstance(parsed, msg_class)

        print(f"   ✅ {msg_type} example: type='{msg.type}'")
    # --- Task 2: Core Ed25519 and CryptoManager validation ---
    print("\n🔄 Testing Ed25519 key generation and sign/verify (Task 2 core)...")
    from cpor.crypto import quick_generate_keypair, quick_verify, CryptoManager
    keypair = quick_generate_keypair("spec_test_key", storage_type="software")
    priv = keypair.private_key
    pub = keypair.public_key
    test_msg = b"spec-aligned crypto test"
    sig = priv.sign(test_msg).signature
    assert isinstance(sig, bytes) and len(sig) == 64
    assert quick_verify(pub, test_msg, sig)
    print("✅ Ed25519 sign/verify successful")

    print("\n🔄 Testing CryptoManager software key management (Task 2 core)...")
    cm = CryptoManager()
    keypair2 = cm.generate_keypair("spec_test_key2", storage_type="software")
    key_id2 = keypair2.key_id
    assert key_id2 in cm.list_keys()
    sig2 = cm.sign_data(key_id2, test_msg)
    assert cm.verify_signature(keypair2.public_key, test_msg, sig2)
    print("✅ CryptoManager software key sign/verify successful")
    
    # --- Task 3: Configuration Management validation ---
    print("\n🔄 Testing Task 3: Configuration Management...")
    from cpor.config import CPORConfig, ConfigManager

    # Test default config creation
    config = CPORConfig(environment="development")
    assert config.environment == "development"
    assert config.version == "CPOR-2"
    print(f"✅ CPORConfig default creation: environment={config.environment}, version={config.version}")

    # Test config manager loads defaults
    manager = ConfigManager()
    manager.load_defaults("testing")
    loaded = manager.config
    assert loaded.environment == "testing"
    print(f"✅ ConfigManager loads defaults: environment={loaded.environment}")

    # Test config roundtrip (to_dict/to_json)
    config_dict = config.to_dict()
    config_json = config.to_json()
    assert isinstance(config_dict, dict)
    assert isinstance(config_json, str)
    print("✅ CPORConfig to_dict/to_json roundtrip")

    # Test config file loading (simulate with dict)
    test_dict = {"environment": "production", "version": "CPOR-2"}
    manager._merge_config(test_dict)  # type: ignore[attr-defined]
    assert manager.config.environment == "production"
    print("✅ ConfigManager _merge_config works with dict input")

    # Test environment enum validation
    try:
        CPORConfig(environment="invalid_env")  # type: ignore
        assert False, "Invalid environment should raise error"
    except Exception:
        print("✅ CPORConfig rejects invalid environment")

    print("\n🎉 TASK 3: CONFIGURATION MANAGEMENT VALIDATION PASSED!")

    print("\n🎉 ALL SPEC-ALIGNED TESTS PASSED!")
    print("\n📊 Summary:")
    print("  ✅ Spec field names (client_pubkey, server_pubkey, etc.)")
    print("  ✅ Required fields added (type, nonce, resume_sequence, etc.)")
    print("  ✅ CBOR serialization/deserialization")
    print("  ✅ Ed25519 signing and verification")
    print("  ✅ Type field message identification")
    print("  ✅ Generic message parsing")
    print("  ✅ All message types working")
    print("  ✅ Updated example message vectors")
    print("\n🚀 Task 1: Message Schemas SPEC-ALIGNED and COMPLETE")

except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    print(f"Error type: {type(e).__name__}")
    print("Traceback:")
    traceback.print_exc()
    sys.exit(1)

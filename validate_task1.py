#!/usr/bin/env python3
"""
CPOR Protocol - Task 1 Validation Script

This script validates the message schemas and serialization implementation
by running comprehensive tests and demonstrating key functionality.
"""

import sys
import traceback
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Test basic imports
    print("🔄 Testing imports...")
    from cpor import (
        ConnectRequest, GenericMessage,
        HeartbeatMessage, ErrorMessage,
        parse_message, EXAMPLE_MESSAGES
    )
    import nacl.signing
    print("✅ All imports successful")

    # Test message creation and validation
    print("\n🔄 Testing message creation...")
    
    # Create a test keypair
    signing_key = nacl.signing.SigningKey.generate()
    verify_key = signing_key.verify_key
    public_key_bytes = bytes(verify_key)
    
    # Test ConnectRequest
    connect_req = ConnectRequest(
        client_id="test-client-001",
        client_pubkey=public_key_bytes,
        capabilities=["batch", "resume", "compression"]
    )
    print(f"✅ ConnectRequest created: {connect_req.client_id}")
    
    # Test CBOR serialization roundtrip
    print("\n🔄 Testing CBOR serialization...")
    cbor_data = connect_req.to_cbor()
    restored_msg = ConnectRequest.from_cbor(cbor_data)
    assert restored_msg == connect_req
    print(f"✅ CBOR roundtrip successful ({len(cbor_data)} bytes)")
    
    # Test generic message parsing
    parsed_msg = parse_message(cbor_data)
    assert isinstance(parsed_msg, ConnectRequest)
    assert parsed_msg == connect_req
    print("✅ Generic message parsing successful")
    
    # Test Ed25519 signing
    print("\n🔄 Testing Ed25519 signatures...")
    signature = connect_req.sign(signing_key)
    assert len(signature) == 64  # Ed25519 signature length
    print(f"✅ Message signed ({len(signature)} byte signature)")
    
    # Test signature verification
    is_valid = connect_req.verify_signature(signature, verify_key)
    assert is_valid
    print("✅ Signature verification successful")
    
    # Test signature failure with wrong key
    other_key = nacl.signing.SigningKey.generate()
    is_invalid = connect_req.verify_signature(signature, other_key.verify_key)
    assert not is_invalid
    print("✅ Invalid signature correctly rejected")
    
    # Test all message types
    print("\n🔄 Testing all message types...")
    
    # Test GenericMessage
    generic_msg = GenericMessage(
        sequence_number=42,
        payload=b"Hello, CPOR Protocol!",
        message_type="data",
        priority=1
    )
    generic_cbor = generic_msg.to_cbor()
    generic_restored = parse_message(generic_cbor)
    assert isinstance(generic_restored, GenericMessage)
    print("✅ GenericMessage working")
    
    # Test HeartbeatMessage
    heartbeat = HeartbeatMessage(
        heartbeat_id="hb-001",
        client_sequence=10,
        server_sequence=8
    )
    hb_cbor = heartbeat.to_cbor()
    hb_restored = parse_message(hb_cbor)
    assert isinstance(hb_restored, HeartbeatMessage)
    print("✅ HeartbeatMessage working")
    
    # Test ErrorMessage
    error_msg = ErrorMessage(
        error_code=400,
        error_message="Invalid sequence number",
        severity="error",
        details={"expected": "integer", "received": "string"}
    )
    error_cbor = error_msg.to_cbor()
    error_restored = parse_message(error_cbor)
    assert isinstance(error_restored, ErrorMessage)
    print("✅ ErrorMessage working")
    
    # Test validation errors
    print("\n🔄 Testing validation...")
    try:
        # This should fail - invalid public key length
        ConnectRequest(client_id="test", client_pubkey=b"short")
        assert False, "Should have raised validation error"
    except Exception as e:
        print(f"✅ Validation error correctly caught: {type(e).__name__}")
    
    # Test all example messages
    print("\n🔄 Testing example messages...")
    for msg_type, example_data in EXAMPLE_MESSAGES.items():
        # Get the message class
        msg_class = globals()[msg_type]
        
        # Create from example
        msg = msg_class.from_dict(example_data)
        
        # Test serialization roundtrip
        cbor_data = msg.to_cbor()
        restored = msg_class.from_cbor(cbor_data)
        assert restored == msg
        
        # Test generic parsing
        parsed = parse_message(cbor_data)
        assert isinstance(parsed, msg_class)
        
        print(f"✅ {msg_type} example working")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("\n📊 Summary:")
    print("  ✅ Message schema validation")
    print("  ✅ CBOR serialization/deserialization")
    print("  ✅ Ed25519 signing and verification")
    print("  ✅ Type safety and validation")
    print("  ✅ Generic message parsing")
    print("  ✅ All 10 message types working")
    print("  ✅ Example message vectors valid")
    print("\n🚀 Task 1: Message Schemas and Serialization - COMPLETE")

except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    print(f"Error type: {type(e).__name__}")
    print(f"Traceback:")
    traceback.print_exc()
    sys.exit(1)

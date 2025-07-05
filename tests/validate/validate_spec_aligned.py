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
        AckMessage, parse_message, EXAMPLE_MESSAGES
    )
    import nacl.signing
    print("✅ All imports successful")

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
        msg_class = globals()[msg_type]
        
        # Create from example
        msg = msg_class.from_dict(example_data)
        
        # Test has type field
        assert hasattr(msg, 'type'), f"Example {msg_type} missing type field"
        
        # Test serialization roundtrip
        cbor_data = msg.to_cbor()
        restored = msg_class.from_cbor(cbor_data)
        assert restored == msg
        
        # Test generic parsing
        parsed = parse_message(cbor_data)
        assert isinstance(parsed, msg_class)
        
        print(f"   ✅ {msg_type} example: type='{msg.type}'")
    
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

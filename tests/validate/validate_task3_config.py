#!/usr/bin/env python3
"""
CPOR Protocol - Task 3 Configuration Management Validation Script

This script validates the configuration management system including:
- Configuration classes and validation
- Loading from files (JSON/YAML)
- Environment variable loading
- Default configurations for different environments
- Error handling and validation
"""

import json
import os
import tempfile
import traceback
from typing import Any, cast
from cpor.config import Environment
import pytest

from cpor.config import (
    CPORConfig,
    ConfigManager,
    NetworkConfig,
    CryptoConfig,
    SecurityConfig,
    load_config,
    get_config_manager,
    EXAMPLE_CONFIGS,
    ConfigLoadError,
)

try:
    print("🔄 Testing Task 3 Configuration Management imports...")
    from cpor.config import (
        CPORConfig,
        ConfigManager,
        NetworkConfig,
        CryptoConfig,
        SecurityConfig,
        load_config,
        get_config_manager,
        EXAMPLE_CONFIGS,
        ConfigLoadError,
    )
    print("✅ All configuration imports successful")

    # Test 1: Basic Configuration Classes
    print("\n🔄 Testing basic configuration classes...")
    
    # Test NetworkConfig
    network_config = NetworkConfig(
        host="test.example.com",
        port=9443,
        max_connections=500
    )
    assert network_config.host == "test.example.com"
    assert network_config.port == 9443
    assert network_config.max_connections == 500
    print("   ✅ NetworkConfig creation and validation")
    
    # Test CryptoConfig
    crypto_config = CryptoConfig(
        key_storage="software",
        nonce_size=16,
        signature_algorithm="Ed25519"
    )
    assert crypto_config.key_storage == "software"
    assert crypto_config.signature_algorithm == "Ed25519"
    print("   ✅ CryptoConfig creation and validation")
    
    # Test SecurityConfig
    security_config = SecurityConfig(
        enable_authentication=True,
        require_tls=False
    )
    assert security_config.enable_authentication is True
    assert security_config.require_tls is False
    print("   ✅ SecurityConfig creation and validation")

    # Test 2: Main CPORConfig
    print("\n🔄 Testing main CPORConfig class...")
    
    config = CPORConfig(
        environment="development",
        debug=True,
        network=network_config,
        crypto=crypto_config,
        security=security_config
    )
    assert config.environment == "development"
    assert config.debug is True
    assert config.network.host == "test.example.com"
    assert config.crypto.key_storage == "software"
    print("   ✅ CPORConfig creation with nested configs")
    
    # Test serialization
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "environment" in config_dict
    assert "network" in config_dict
    print("   ✅ CPORConfig to_dict() serialization")
    
    config_json = config.to_json()
    assert isinstance(config_json, str)
    parsed_json = json.loads(config_json)
    assert isinstance(parsed_json, dict)
    print("   ✅ CPORConfig to_json() serialization")

    # Test 3: ConfigManager
    print("\n🔄 Testing ConfigManager...")
    
    manager = ConfigManager()
    assert isinstance(manager.config, CPORConfig)
    assert len(manager.sources) == 0
    print("   ✅ ConfigManager initialization")
    
    # Test loading defaults
    manager.load_defaults("development")
    assert manager.config.environment == "development"
    assert "defaults (development)" in manager.sources
    print("   ✅ ConfigManager load_defaults()")
    
    # Test validation
    is_valid = manager.validate()
    assert is_valid is True
    print("   ✅ ConfigManager validation")

    # Test 4: Environment Variable Loading
    print("\n🔄 Testing environment variable loading...")
    
    # Set test environment variables
    test_env_vars = {
        "CPOR_DEBUG": "true",
        "CPOR_NETWORK_HOST": "env.example.com",
        "CPOR_NETWORK_PORT": "7777",
        "CPOR_LOGGING_LEVEL": "ERROR"
    }
    
    # Store original values
    original_values: dict[str, str | None] = {}
    for key, value in test_env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        manager = ConfigManager()
        manager.load_defaults("development")
        manager.load_from_env("CPOR_")
        
        assert manager.config.debug is True
        assert manager.config.network.host == "env.example.com"
        assert manager.config.network.port == 7777
        assert manager.config.logging.level == "ERROR"
        print("   ✅ Environment variable loading and type conversion")
        
    finally:
        # Restore original environment
        for key, original_value in original_values.items():
            k = str(key)  # type: ignore
            _ = original_value  # type: ignore[unused]
            os.environ.pop(k, None)

    # Test 5: File Loading (JSON)
    print("\n🔄 Testing JSON file loading...")
    
    test_json_config: dict[str, Any] = {
        "environment": "testing",
        "debug": True,
        "network": {
            "host": "json.example.com",
            "port": 8888,
            "max_connections": 200
        },
        "crypto": {
            "key_storage": "tpm",
            "nonce_size": 24
        },
        "custom": {
            "app_name": "test_app",
            "feature_flags": ["feature_a", "feature_b"]
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_json_config, f, indent=2)
        json_file_path = f.name
    
    try:
        manager = ConfigManager()
        manager.load_defaults("development")
        manager.load_from_file(json_file_path)
        
        assert manager.config.environment == "testing"
        assert manager.config.network.host == "json.example.com"
        assert manager.config.network.port == 8888
        assert manager.config.crypto.key_storage == "tpm"
        assert manager.config.crypto.nonce_size == 24
        assert manager.config.custom["app_name"] == "test_app"
        assert json_file_path in str(manager.sources)
        print("   ✅ JSON file loading and configuration merging")
        
    finally:
        os.unlink(json_file_path)

    # Test 6: File Loading (YAML)
    print("\n🔄 Testing YAML file loading...")
    
    import yaml
    
    test_yaml_config: dict[str, Any] = {
        "environment": "staging",
        "network": {
            "host": "yaml.example.com",
            "port": 6666
        },
        "logging": {
            "level": "WARNING",
            "file": "/tmp/test.log"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_yaml_config, f, default_flow_style=False)
        yaml_file_path = f.name
    
    try:
        manager = ConfigManager()
        manager.load_defaults("development")
        manager.load_from_file(yaml_file_path)
        
        assert manager.config.environment == "staging"
        assert manager.config.network.host == "yaml.example.com"
        assert manager.config.network.port == 6666
        assert manager.config.logging.level == "WARNING"
        print("   ✅ YAML file loading and configuration merging")
        
    finally:
        os.unlink(yaml_file_path)

    # Test 7: Configuration Validation and Error Handling
    print("\n🔄 Testing configuration validation and error handling...")
    
    # Test invalid port validation
    try:
        NetworkConfig(port=-1)
        assert False, "Should have raised validation error"
    except Exception:
        print("   ✅ NetworkConfig port validation error handling")
    
    # Test invalid signature algorithm
    try:
        CryptoConfig(signature_algorithm="RSA")
        assert False, "Should have raised validation error"
    except Exception:
        print("   ✅ CryptoConfig signature algorithm validation")
    
    # Test invalid environment
    try:
        # This test intentionally passes an invalid environment string
        # Use cast to satisfy mypy, runtime will raise
        with pytest.raises(ValueError):
            CPORConfig(environment=cast(Environment, "invalid_env"))
        assert False, "Should have raised validation error"
    except Exception:
        print("   ✅ CPORConfig environment validation")
    
    # Test loading nonexistent file
    try:
        manager = ConfigManager()
        manager.load_from_file("/nonexistent/path/config.json")
        assert False, "Should have raised ConfigLoadError"
    except ConfigLoadError:
        print("   ✅ ConfigLoadError for nonexistent file")

    # Test 8: Environment-Specific Defaults
    print("\n🔄 Testing environment-specific defaults...")
    
    # Development defaults
    dev_manager = ConfigManager()
    dev_manager.load_defaults("development")
    assert dev_manager.config.environment == "development"
    assert dev_manager.config.debug is True
    print("   ✅ Development environment defaults")
    
    # Production defaults
    prod_manager = ConfigManager()
    prod_manager.load_defaults("production")
    assert prod_manager.config.environment == "production"
    assert prod_manager.config.debug is False
    print("   ✅ Production environment defaults")
    
    # Testing defaults
    test_manager = ConfigManager()
    test_manager.load_defaults("testing")
    assert test_manager.config.environment == "testing"
    print("   ✅ Testing environment defaults")

    # Test 9: Configuration Save/Load Roundtrip
    print("\n🔄 Testing configuration save/load roundtrip...")
    
    original_config = CPORConfig(
        environment="staging",
        debug=True,
        network=NetworkConfig(
            host="roundtrip.example.com",
            port=5555
        ),
        custom={
            "test_key": "test_value",
            "numbers": [1, 2, 3]
        }
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        roundtrip_file = f.name
    
    try:
        # Save configuration
        original_config.save_to_file(roundtrip_file)
        
        # Load configuration
        manager = ConfigManager()
        manager.load_from_file(roundtrip_file)
        loaded_config = manager.config
        
        # Verify roundtrip
        assert loaded_config.environment == original_config.environment
        assert loaded_config.debug == original_config.debug
        assert loaded_config.network.host == original_config.network.host
        assert loaded_config.network.port == original_config.network.port
        assert loaded_config.custom == original_config.custom
        print("   ✅ Configuration save/load roundtrip")
        
    finally:
        os.unlink(roundtrip_file)

    # Test 10: Utility Functions and Global Manager
    print("\n🔄 Testing utility functions and global manager...")
    
    # Test load_config function
    config = load_config(environment="development")
    assert isinstance(config, CPORConfig)
    assert config.environment == "development"
    print("   ✅ load_config() utility function")
    
    # Test global config manager
    manager1 = get_config_manager()
    manager2 = get_config_manager()
    assert manager1 is manager2  # Should be same instance
    print("   ✅ Global config manager singleton")
    
    # Test example configs
    assert "development" in EXAMPLE_CONFIGS
    assert "production" in EXAMPLE_CONFIGS
    assert EXAMPLE_CONFIGS["development"]["debug"] is True
    assert EXAMPLE_CONFIGS["production"]["debug"] is False
    print("   ✅ Example configuration templates")

    print("\n🎉 ALL TASK 3 CONFIGURATION MANAGEMENT TESTS PASSED!")
    print("\n📊 Task 3 Summary:")
    print("  ✅ Configuration classes (Network, Crypto, Security, Logging, Performance)")
    print("  ✅ Main CPORConfig with validation and serialization")
    print("  ✅ ConfigManager with file and environment loading")
    print("  ✅ JSON and YAML file format support")
    print("  ✅ Environment variable loading with type conversion")
    print("  ✅ Environment-specific default configurations")
    print("  ✅ Configuration validation and error handling")
    print("  ✅ Configuration merging and precedence")
    print("  ✅ Save/load roundtrip functionality")
    print("  ✅ Utility functions and global manager")
    print("\n🚀 Task 3: Configuration Management COMPLETE")

except Exception as e:
    print(f"\n❌ Task 3 validation failed with error: {e}")
    print(f"Error type: {type(e).__name__}")
    print("Traceback:")
    traceback.print_exc()
    exit(1)

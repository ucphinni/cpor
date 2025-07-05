"""
Tests for CPOR Configuration Management

This module tests the configuration management system including validation,
loading from files, environment variables, and default configurations.
"""

import json
import os
import tempfile
import pytest
from typing import Any, Dict, cast
from cpor.config import Environment

from cpor.config import (
    CPORConfig,
    ConfigManager,
    NetworkConfig,
    CryptoConfig,
    LoggingConfig,
    SecurityConfig,
    PerformanceConfig,
    load_config,
    get_config_manager,
    set_config_manager,
    EXAMPLE_CONFIGS,
    ConfigValidationError,
    ConfigLoadError,
)


class TestNetworkConfig:
    """Test NetworkConfig validation and defaults."""
    
    def test_default_values(self):
        """Test default network configuration values."""
        config = NetworkConfig()
        assert config.host == "localhost"
        assert config.port == 8443
        assert config.max_connections == 100
        assert config.connection_timeout == 30.0
        assert config.keepalive_interval == 60.0
        assert config.max_message_size == 1048576
        assert config.buffer_size == 8192
    
    def test_valid_configuration(self):
        """Test valid network configuration."""
        config = NetworkConfig(
            host="0.0.0.0",
            port=9443,
            max_connections=500,
            connection_timeout=60.0,
            keepalive_interval=30.0,
            max_message_size=2048576,
            buffer_size=16384
        )
        assert config.host == "0.0.0.0"
        assert config.port == 9443
        assert config.max_connections == 500
    
    def test_invalid_port(self):
        """Test invalid port validation."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            NetworkConfig(port=0)
        
        with pytest.raises(Exception):
            NetworkConfig(port=70000)
    
    def test_invalid_host(self):
        """Test invalid host validation."""
        with pytest.raises(Exception):
            NetworkConfig(host="")
        
        with pytest.raises(Exception):
            NetworkConfig(host="   ")
    
    def test_host_normalization(self):
        """Test host string normalization."""
        config = NetworkConfig(host="  localhost  ")
        assert config.host == "localhost"


class TestCryptoConfig:
    """Test CryptoConfig validation and defaults."""
    
    def test_default_values(self):
        """Test default crypto configuration values."""
        config = CryptoConfig()
        assert config.key_storage == "software"
        assert config.tpm_device is None
        assert config.key_derivation_iterations == 100000
        assert config.nonce_size == 16
        assert config.session_key_size == 32
        assert config.signature_algorithm == "Ed25519"
        assert config.enable_key_rotation is True
        assert config.key_rotation_interval == 86400
    
    def test_tpm_configuration(self):
        """Test TPM configuration."""
        config = CryptoConfig(
            key_storage="tpm",
            tpm_device="/dev/tpm0"
        )
        assert config.key_storage == "tpm"
        assert config.tpm_device == "/dev/tpm0"
    
    def test_invalid_signature_algorithm(self):
        """Test invalid signature algorithm validation."""
        with pytest.raises(Exception):
            CryptoConfig(signature_algorithm="RSA")
    
    def test_invalid_nonce_size(self):
        """Test invalid nonce size validation."""
        with pytest.raises(Exception):
            CryptoConfig(nonce_size=4)  # Too small
        
        with pytest.raises(Exception):
            CryptoConfig(nonce_size=128)  # Too large


class TestSecurityConfig:
    """Test SecurityConfig validation and defaults."""
    
    def test_default_values(self):
        """Test default security configuration values."""
        config = SecurityConfig()
        assert config.enable_authentication is True
        assert config.enable_encryption is True
        assert config.max_auth_attempts == 3
        assert config.auth_timeout == 300.0
        assert config.session_timeout == 3600.0
        assert config.require_tls is True
        assert len(config.allowed_cipher_suites) > 0
    
    def test_tls_disabled_configuration(self):
        """Test configuration with TLS disabled."""
        config = SecurityConfig(
            require_tls=False,
            certificate_path=None,
            private_key_path=None
        )
        assert config.require_tls is False
        assert config.certificate_path is None
        assert config.private_key_path is None


class TestCPORConfig:
    """Test main CPORConfig class."""
    
    def test_default_configuration(self):
        """Test default CPOR configuration."""
        config = CPORConfig()
        assert config.environment == "development"
        assert config.version == "CPOR-2"
        assert config.debug is False
        assert isinstance(config.network, NetworkConfig)
        assert isinstance(config.crypto, CryptoConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.custom, dict)
    
    def test_environment_validation(self):
        """Test environment validation."""
        # Valid environments
        for env in ["development", "testing", "staging", "production"]:
            config = CPORConfig(environment=cast(Environment, env))
            assert config.environment == env
        
        # Invalid environment
        # This test intentionally passes an invalid environment string
        # Use cast to satisfy mypy, runtime will raise
        with pytest.raises(ValueError):
            CPORConfig(environment=cast(Environment, "invalid"))
    
    def test_version_validation(self):
        """Test protocol version validation."""
        config = CPORConfig(version="CPOR-2")
        assert config.version == "CPOR-2"
        
        with pytest.raises(Exception):
            CPORConfig(version="CPOR-1")
    
    def test_nested_configuration(self):
        """Test nested configuration creation."""
        config = CPORConfig(
            environment="production",
            network=NetworkConfig(host="0.0.0.0", port=443),
            crypto=CryptoConfig(key_storage="tpm"),
            custom={"app_name": "test_app", "version": "1.0.0"}
        )
        
        assert config.environment == "production"
        assert config.network.host == "0.0.0.0"
        assert config.network.port == 443
        assert config.crypto.key_storage == "tpm"
        assert config.custom["app_name"] == "test_app"
    
    def test_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = CPORConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "environment" in config_dict
        assert "network" in config_dict
        assert "crypto" in config_dict
        assert isinstance(config_dict["network"], dict)
    
    def test_to_json(self):
        """Test configuration to JSON conversion."""
        config = CPORConfig()
        json_str = config.to_json()
        
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "environment" in parsed


class TestConfigManager:
    """Test ConfigManager functionality."""
    
    def test_default_initialization(self):
        """Test default ConfigManager initialization."""
        manager = ConfigManager()
        assert isinstance(manager.config, CPORConfig)
        assert manager.config.environment == "development"
        assert len(manager.sources) == 0
    
    def test_custom_config_initialization(self):
        """Test ConfigManager with custom config."""
        custom_config = CPORConfig(environment="production")
        manager = ConfigManager(custom_config)
        assert manager.config.environment == "production"
    
    def test_load_defaults(self):
        """Test loading default configurations."""
        manager = ConfigManager()
        
        # Test development defaults
        manager.load_defaults("development")
        assert manager.config.environment == "development"
        assert manager.config.debug is True
        assert "defaults (development)" in manager.sources
        
        # Test production defaults
        manager.load_defaults("production")
        assert manager.config.environment == "production"
        assert manager.config.debug is False
    
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        # Set test environment variables
        test_env = {
            "CPOR_DEBUG": "true",
            "CPOR_NETWORK_HOST": "test.example.com",
            "CPOR_NETWORK_PORT": "9999",
            "CPOR_LOGGING_LEVEL": "ERROR"
        }
        
        # Temporarily set environment variables
        original_env: dict[str, str | None] = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            manager = ConfigManager()
            manager.load_defaults("development")
            manager.load_from_env("CPOR_")
            
            assert manager.config.debug is True
            assert manager.config.network.host == "test.example.com"
            assert manager.config.network.port == 9999
            assert manager.config.logging.level == "ERROR"
            assert any("environment" in source for source in manager.sources)
        
        finally:
            # Restore original environment
            for key, value in original_env.items():
                k = str(key)  # type: ignore
                _ = value  # type: ignore[unused]
                os.environ.pop(k, None)
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        test_config: Dict[str, Any] = {
            "environment": "testing",
            "debug": True,
            "network": {
                "host": "json.example.com",
                "port": 8888
            },
            "custom": {
                "test_value": "from_json"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            manager.load_defaults("development")
            manager.load_from_file(temp_path)
            
            assert manager.config.environment == "testing"
            assert manager.config.network.host == "json.example.com"
            assert manager.config.network.port == 8888
            assert manager.config.custom["test_value"] == "from_json"
            assert temp_path in str(manager.sources)
        
        finally:
            os.unlink(temp_path)
    
    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        import yaml
        
        test_config: Dict[str, Any] = {
            "environment": "testing",
            "network": {
                "host": "yaml.example.com",
                "port": 7777
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            manager.load_defaults("development")
            manager.load_from_file(temp_path)
            
            assert manager.config.environment == "testing"
            assert manager.config.network.host == "yaml.example.com"
            assert manager.config.network.port == 7777
        
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        manager = ConfigManager()
        
        with pytest.raises(ConfigLoadError):
            manager.load_from_file("/nonexistent/path/config.json")
    
    def test_load_invalid_json_file(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            with pytest.raises(ConfigLoadError):
                manager.load_from_file(temp_path)
        
        finally:
            os.unlink(temp_path)
    
    def test_validation(self):
        """Test configuration validation."""
        manager = ConfigManager()
        manager.load_defaults("development")
        
        # Valid configuration should pass
        assert manager.validate() is True
        
        # Create invalid configuration by direct manipulation
        manager._config.network.port = -1  # type: ignore[attr-defined]
        
        with pytest.raises(ConfigValidationError):
            manager.validate()
    
    def test_config_merge(self):
        """Test configuration merging."""
        manager = ConfigManager()
        manager.load_defaults("development")
        
        # Initial values
        assert manager.config.network.host == "localhost"
        assert manager.config.network.port == 8443
        
        # Merge with partial update
        partial_config = {
            "network": {
                "host": "merged.example.com"
            },
            "custom": {
                "new_field": "merged_value"
            }
        }
        
        manager._merge_config(partial_config)  # type: ignore[attr-defined]
        
        # Host should be updated, port should remain
        assert manager.config.network.host == "merged.example.com"
        assert manager.config.network.port == 8443
        assert manager.config.custom["new_field"] == "merged_value"


class TestConfigUtilities:
    """Test configuration utility functions."""
    
    def test_load_config_function(self):
        """Test load_config convenience function."""
        # Test default loading
        config = load_config(environment="development")
        assert isinstance(config, CPORConfig)
        assert config.environment == "development"
    
    def test_get_set_config_manager(self):
        """Test global config manager functions."""
        # Get default manager
        manager1 = get_config_manager()
        assert isinstance(manager1, ConfigManager)
        
        # Should return same instance
        manager2 = get_config_manager()
        assert manager1 is manager2
        
        # Set custom manager
        custom_manager = ConfigManager(CPORConfig(environment="testing"))
        set_config_manager(custom_manager)
        
        manager3 = get_config_manager()
        assert manager3 is custom_manager
        assert manager3.config.environment == "testing"
    
    def test_example_configs(self):
        """Test example configuration templates."""
        assert "development" in EXAMPLE_CONFIGS
        assert "production" in EXAMPLE_CONFIGS
        
        # Development config should have debug enabled
        dev_config = EXAMPLE_CONFIGS["development"]
        assert dev_config["debug"] is True
        assert dev_config["environment"] == "development"
        
        # Production config should have debug disabled
        prod_config = EXAMPLE_CONFIGS["production"]
        assert prod_config["debug"] is False
        assert prod_config["environment"] == "production"


class TestConfigSaveLoad:
    """Test configuration save/load roundtrips."""
    
    def test_save_load_json_roundtrip(self):
        """Test save and load JSON configuration roundtrip."""
        original_config = CPORConfig(
            environment="testing",
            debug=True,
            network=NetworkConfig(host="test.example.com", port=9999),
            custom={"test": "value"}
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save configuration
            original_config.save_to_file(temp_path)
            
            # Load configuration
            manager = ConfigManager()
            manager.load_from_file(temp_path)
            loaded_config = manager.config
            
            # Compare key values
            assert loaded_config.environment == original_config.environment
            assert loaded_config.debug == original_config.debug
            assert loaded_config.network.host == original_config.network.host
            assert loaded_config.network.port == original_config.network.port
            assert loaded_config.custom == original_config.custom
        
        finally:
            os.unlink(temp_path)
    
    def test_save_load_yaml_roundtrip(self):
        """Test save and load YAML configuration roundtrip."""
        original_config = CPORConfig(
            environment="staging",
            network=NetworkConfig(host="staging.example.com")
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save configuration
            original_config.save_to_file(temp_path)
            
            # Load configuration
            manager = ConfigManager()
            manager.load_from_file(temp_path)
            loaded_config = manager.config
            
            # Compare key values
            assert loaded_config.environment == original_config.environment
            assert loaded_config.network.host == original_config.network.host
        
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__])

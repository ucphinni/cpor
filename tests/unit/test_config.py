"""
Tests for CPOR Configuration Management

This module tests the configuration management system including validation,
loading from files, environment variables, and default configurations.
"""

import json
import os
import tempfile
import warnings
import pytest
from typing import Any, Dict, cast
from pathlib import Path
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
    LogLevel,  # Import LogLevel for type checking
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
    
    def test_host_empty_string(self):
        """Test that empty host string raises ValueError."""
        with pytest.raises(ValueError, match="Host must be a non-empty string"):
            NetworkConfig(host="")
    
    def test_host_whitespace_string(self):
        """Test that whitespace-only host string raises ValueError."""
        with pytest.raises(ValueError, match="Host must be a non-empty string"):
            NetworkConfig(host="   ")
    
    def test_host_normalization(self):
        """Test host normalization logic."""
        config = NetworkConfig(host="  localhost  ")
        assert config.host == "localhost"

    def test_invalid_port(self):
        """Test that invalid port raises ValueError."""
        with pytest.raises(ValueError):
            NetworkConfig(port=70000)
    
    def test_invalid_connection_timeout(self):
        """Test that invalid connection timeout raises ValueError."""
        with pytest.raises(ValueError):
            NetworkConfig(connection_timeout=0.05)
    
    def test_invalid_keepalive_interval(self):
        """Test that invalid keepalive interval raises ValueError."""
        with pytest.raises(ValueError):
            NetworkConfig(keepalive_interval=0.5)
    
    def test_invalid_max_message_size(self):
        """Test that invalid max message size raises ValueError."""
        with pytest.raises(ValueError):
            NetworkConfig(max_message_size=512)
    
    def test_invalid_buffer_size(self):
        """Test that invalid buffer size raises ValueError."""
        with pytest.raises(ValueError):
            NetworkConfig(buffer_size=256)

    def test_invalid_max_connections(self):
        """Test that invalid max connections raises ValueError."""
        with pytest.raises(ValueError):
            NetworkConfig(max_connections=0)


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

    def test_invalid_key_rotation_interval(self):
        """Test that invalid key rotation interval raises ValueError."""
        with pytest.raises(ValueError):
            CryptoConfig(key_rotation_interval=3599)

    def test_tpm_device_warning_logged(self):
        """Test TPM device warning when TPM storage is selected but no device specified."""
        import logging
        from io import StringIO

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger()  # Define the logger
        logger.addHandler(handler)

        config = CryptoConfig(key_storage="tpm", tpm_device=None)
        assert config.key_storage == "tpm"
        assert config.tpm_device is None

        logger.removeHandler(handler)
        log_contents = log_stream.getvalue()
        assert "TPM storage selected but no TPM device specified" in log_contents


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
    
    def test_invalid_auth_timeout(self):
        """Test that invalid authentication timeout raises ValueError."""
        with pytest.raises(ValueError):
            SecurityConfig(auth_timeout=5.0)

    def test_invalid_session_timeout(self):
        """Test that invalid session timeout raises ValueError."""
        with pytest.raises(ValueError):
            SecurityConfig(session_timeout=59.0)

    def test_invalid_certificate_path(self):
        """Test that invalid certificate path raises ValueError."""
        with pytest.raises(ValueError, match="TLS certificate file not found"):
            SecurityConfig(certificate_path="/invalid/path/to/cert.pem")

    def test_invalid_private_key_path(self):
        """Test that invalid TLS private key path raises ValueError."""
        with pytest.raises(ValueError, match="Value error, TLS private_key file not found: /invalid/path/to/key.pem"):
            SecurityConfig(private_key_path="/invalid/path/to/key.pem")

    def test_tls_certificate_not_found(self):
        """Test that missing TLS certificate file raises ValueError."""
        with pytest.raises(ValueError, match="TLS certificate file not found"):
            SecurityConfig(certificate_path="/nonexistent/cert.pem")

    def test_tls_private_key_not_found(self):
        """Test that missing TLS private key file raises ValueError."""
        with pytest.raises(ValueError, match="Value error, TLS private_key file not found: /nonexistent/key.pem"):
            SecurityConfig(private_key_path="/nonexistent/key.pem")

    def test_invalid_environment(self):
        """Test invalid environment raises ValueError."""
        with pytest.raises(ValueError, match="Input should be 'development', 'testing', 'staging' or 'production'"):
            CPORConfig(environment=cast(Environment, "invalid_env"))

    def test_validate_environment(self):
        with pytest.raises(ValueError, match="Input should be 'development', 'testing', 'staging' or 'production'"):
            CPORConfig(environment=cast(Environment, "invalid"))


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
    
    def test_invalid_environment(self):
        """Test invalid environment raises ValueError."""
        with pytest.raises(ValueError, match="Input should be 'development', 'testing', 'staging' or 'production'"):
            CPORConfig(environment=cast(Environment, "invalid_env"))

    def test_invalid_version(self):
        """Test invalid protocol version raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported protocol version"):
            CPORConfig(version="CPOR-1")

    def test_logging_file_validation(self):
        """Test invalid log file path raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log file path"):
            LoggingConfig(file="/invalid/path/to/logfile.log")

    def test_invalid_logging_level(self):
        """Test that invalid logging level raises ValueError."""
        with pytest.raises(ValueError, match="Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'"):
            LoggingConfig(level=cast(LogLevel, "INVALID"))

    def test_invalid_debug_mode_in_production(self):
        """Test that debug mode in production raises a warning."""
        with pytest.warns(UserWarning, match="Debug mode enabled in production environment"):
            config = CPORConfig(environment="production", debug=True)
            config.__post_init_post_parse__()

    def test_invalid_logging_level_in_production(self):
        """Test that debug logging level in production raises a warning."""
        with pytest.warns(UserWarning, match="Debug logging enabled in production environment"):
            config = CPORConfig(environment="production", logging=LoggingConfig(level="DEBUG"))
            config.__post_init_post_parse__()

    def test_post_init_production_debug_warning(self):
        """Test __post_init_post_parse__ for production debug warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = CPORConfig(environment="production", debug=True)
            config.__post_init_post_parse__()
            assert len(w) == 1
            assert "Debug mode enabled in production environment" in str(w[0].message)

    def test_post_init_production_logging_warning(self):
        with pytest.warns(UserWarning, match="Debug logging enabled in production environment"):
            config = CPORConfig(environment="production", logging=LoggingConfig(level="DEBUG"))
            config.__post_init_post_parse__()

    def test_post_init_development_defaults(self):
        config = CPORConfig(environment="development")
        config.__post_init_post_parse__()
        assert config.debug is True
        assert config.logging.level == "DEBUG"

    def test_validate_version(self):
        with pytest.raises(ValueError, match="Unsupported protocol version"):
            CPORConfig(version="INVALID")

    def test_validate_environment(self):
        with pytest.raises(ValueError, match="Input should be 'development', 'testing', 'staging' or 'production'"):
            CPORConfig(environment=cast(Environment, "invalid"))

    from pathlib import Path

    def test_save_to_file_yaml(self, tmp_path: Path):
        config = CPORConfig()
        file_path = tmp_path / "config.yaml"
        config.save_to_file(file_path)
        assert file_path.exists()
        assert file_path.suffix == ".yaml"

    def test_save_to_file_json(self, tmp_path: "Path"):
        config = CPORConfig()
        file_path = tmp_path / "config.json"
        config.save_to_file(file_path)
        assert file_path.exists()
        assert file_path.suffix == ".json"

    def test_load_from_file_valid(self, tmp_path: "Path"):
        file_path = tmp_path / "config.yaml"
        file_path.write_text("environment: production\nversion: CPOR-2")
        manager = ConfigManager()
        manager.load_from_file(file_path)
        assert manager.config.environment == "production"
        assert manager.config.version == "CPOR-2"

    def test_load_from_file_invalid(self, tmp_path: "Path"):
        file_path = tmp_path / "config.yaml"
        file_path.write_text("invalid_yaml: [")
        manager = ConfigManager()
        with pytest.raises(ConfigLoadError):
            manager.load_from_file(file_path)


    def test_load_defaults(self):
        manager = ConfigManager()
        manager.load_defaults("production")
        assert manager.config.environment == "production"
        assert manager.config.logging.level == "WARNING"

    def test_deep_merge(self):
        manager = ConfigManager()
        base: dict[str, dict[str, int | str]] = {"network": {"host": "localhost", "port": 8443}}
        update: dict[str, dict[str, int]] = {"network": {"port": 9443, "max_connections": 100}}
        result = manager._deep_merge(base, update) # type: ignore
        assert result["network"]["host"] == "localhost"
        assert result["network"]["port"] == 9443
        assert result["network"]["max_connections"] == 100


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

    def test_post_init_post_parse_call(self):
        """Test explicit call to __post_init_post_parse__ method."""
        config = CPORConfig(environment="development")
        config.__post_init_post_parse__()
        assert config.debug is True
        assert config.logging.level == "DEBUG"

    def test_save_to_file_unsupported_format3(self, tmp_path: Path):
        """Test save_to_file with unsupported file format."""
        config = CPORConfig()
        file_path = tmp_path / "config.txt"
        with pytest.raises(ConfigLoadError, match="Unsupported file format"):
            config.save_to_file(file_path)

    def test_merge_config_deeply_nested(self):
        """Test _merge_config with deeply nested dictionaries."""
        manager = ConfigManager()
        base: dict[str, Any] = {"network": {"host": "localhost", "settings": {"timeout": 30}}}
        update: dict[str, Any] = {"network": {"settings": {"timeout": 60, "retries": 5}}}
        result = manager._deep_merge(base, update)  # type: ignore
        assert result["network"]["settings"]["timeout"] == 60
        assert result["network"]["settings"]["retries"] == 5

    def test_set_nested_value_edge_cases2(self):
        """Test _set_nested_value with edge cases."""
        manager = ConfigManager()
        config = {}
        manager._set_nested_value(config, "network_host", "localhost")  # type: ignore
        assert config["network"]["host"] == "localhost"

        manager._set_nested_value(config, "network_port", "8443")  # type: ignore
        assert config["network"]["port"] == 8443

        manager._set_nested_value(config, "network_timeout", "30.5")  # type: ignore
        assert config["network"]["timeout"] == 30.5

    def test_post_init_production_defaults(self):
        """Test production-specific defaults in __post_init_post_parse__."""
        config = CPORConfig(environment="production", debug=False, logging=LoggingConfig(level="INFO"))
        config.__post_init_post_parse__()
        assert config.debug is False
        assert config.logging.level == "INFO"

    def test_post_init_production_warnings(self):
        """Test production environment post-init logic."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = CPORConfig(environment="production", debug=True, logging=LoggingConfig(level="DEBUG"))
            config.__post_init_post_parse__()
            assert len(w) == 2
            assert "Debug mode enabled in production environment" in str(w[0].message)
            assert "Debug logging enabled in production environment" in str(w[1].message)

    def test_post_init_development_defaults(self):
        config = CPORConfig(environment="development", debug=False, logging=LoggingConfig(level="INFO"))
        config.__post_init_post_parse__()
        assert config.debug is True
        assert config.logging.level == "DEBUG"

    def test_validate_and_normalize_host_empty(self):
        """Test validate_and_normalize_host for empty host."""
        with pytest.raises(ValueError, match="Host must be a non-empty string"):
            NetworkConfig(host="")

    def test_validate_log_file_invalid(self):
        """Test validate_log_file for invalid paths and permissions."""
        with pytest.raises(ValueError, match="Invalid log file path"):
            LoggingConfig(file="/invalid/path/to/logfile.log")

    def test_validate_signature_algorithm_unsupported(self):
        """Test validate_signature_algorithm for unsupported algorithms."""
        with pytest.raises(ValueError, match="Only Ed25519 signature algorithm is supported"):
            CryptoConfig(signature_algorithm="RSA")

    def test_validate_tpm_device_missing(self):
        """Test validate_tpm_device for missing TPM device."""
        config = CryptoConfig(key_storage="tpm", tpm_device=None)
        assert config.key_storage == "tpm"
        assert config.tpm_device is None

    def test_save_to_file_unsupported_format(self, tmp_path: Path):
        """Test save_to_file with unsupported file format."""
        config = CPORConfig()
        with pytest.raises(ConfigLoadError, match="Unsupported file format"):
            config.save_to_file("config.unsupported")

    def test_parse_yaml_json_errors(self):
        """Test YAML and JSON parsing errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid_yaml: [")
            temp_path = f.name
        try:
            with pytest.raises(ConfigLoadError, match="Failed to parse YAML file"):
                ConfigManager().load_from_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_invalid_config_structure(self):
        """Test invalid configuration file structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("[]")
            temp_path = f.name
        try:
            with pytest.raises(ConfigLoadError, match="Configuration file must contain a dictionary/object"):
                ConfigManager().load_from_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_deep_merge_nested_dicts(self):
        """Test deeply nested dictionary merging."""
        manager = ConfigManager()
        base: dict[str, dict[str, object]] = {"network": {"host": "localhost", "settings": {"timeout": 30}}}
        update: dict[str, dict[str, object]] = {"network": {"settings": {"timeout": 60, "retries": 5}}}
        result = manager._deep_merge(base, update) # type: ignore
        assert result["network"]["settings"]["timeout"] == 60
        assert result["network"]["settings"]["retries"] == 5

    def test_set_nested_value_edge_cases(self):
        """Test _set_nested_value for edge cases."""
        manager = ConfigManager()
        config: dict[str, Any] = {}
        manager._set_nested_value(config, "network_host", "localhost") # type: ignore
        manager._set_nested_value(config, "network_port", "8443") # type: ignore
        manager._set_nested_value(config, "debug", "true") # type: ignore
        assert config["network"]["host"] == "localhost"
        assert config["network"]["port"] == 8443
        assert config["debug"] is True

    def test_validate_config_failures(self):
        """Test configuration validation failures."""
        manager = ConfigManager()
        manager.load_defaults("development")
        manager._config.network.port = -1 # type: ignore
        with pytest.raises(ConfigValidationError, match="Configuration validation failed"):
            manager.validate()

    def test_save_to_file_invalid_path(self):
        """Test save_to_file with an invalid path (should raise an error)."""
        config = CPORConfig()
        with pytest.raises(ConfigLoadError):
            config.save_to_file("/this/path/does/not/exist/config.yaml")

    def test_load_from_file_unsupported_extension(self, tmp_path: Path):
        """Test loading from a file with an unsupported extension."""
        file_path = tmp_path / "config.unsupported"
        file_path.write_text("environment: production\nversion: CPOR-2")
        manager = ConfigManager()
        with pytest.raises(ConfigLoadError, match="Unsupported file format"):
            manager.load_from_file(file_path)

    def test_merge_config_with_non_dict(self):
        """Test _deep_merge with a non-dict update (should raise AttributeError)."""
        manager = ConfigManager()
        base = {"network": {"host": "localhost"}}
        update = ["not", "a", "dict"]
        with pytest.raises(AttributeError):
            manager._deep_merge(base, update)  # type: ignore

    def test_set_nested_value_type_casting(self):
        """Test _set_nested_value with various type castings."""
        manager = ConfigManager()
        config: dict[str, Any] = {}
        manager._set_nested_value(config, "performance_memory_limit", "1024")  # type: ignore
        assert "performance" in config
        assert "memory" in config['performance']
        assert "limit" in config['performance']['memory']
        assert config["performance"]["memory"]["limit"] == 1024

        manager._set_nested_value(config, "performance_enable_metrics", "false")  # type: ignore
        assert "enable" in config['performance']
        assert "metrics" in config['performance']['enable']
        assert config["performance"]["enable"]["metrics"] is False

    def test_load_env_with_partial_vars(self):
        """Test loading from environment with only some variables set."""
        os.environ["CPOR_NETWORK_HOST"] = "envhost"
        manager = ConfigManager()
        manager.load_defaults("development")
        manager.load_from_env("CPOR_")
        assert manager.config.network.host == "envhost"
        del os.environ["CPOR_NETWORK_HOST"]

    def test_load_defaults_all_environments(self):
        """Test loading defaults for all environments."""
        manager = ConfigManager()
        for env in ["development", "testing", "staging", "production"]:
            e: Environment = cast(Environment, env)
            manager.load_defaults(e)
            assert manager.config.environment == e

    def test_validate_config_invalid_type(self):
        """Test config validation with wrong type."""
        manager = ConfigManager()
        manager._config.network.port = "not_an_int"  # type: ignore
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with pytest.raises(ConfigValidationError):
                manager.validate()

    def test_deep_merge_missing_keys(self):
        """Test _deep_merge when update has keys not in base."""
        manager = ConfigManager()
        base = {"network": {"host": "localhost"}}
        update = {"crypto": {"key_storage": "tpm"}}
        result = manager._deep_merge(base, update)  # type: ignore
        assert result["network"]["host"] == "localhost"
        assert result["crypto"]["key_storage"] == "tpm"

    def test_set_nested_value_multiple_underscores(self):
        """Test _set_nested_value with keys containing multiple underscores."""
        manager = ConfigManager()
        config = {}
        manager._set_nested_value(config, "performance_memory_limit_soft", "2048")  # type: ignore
        assert config["performance"]["memory"]["limit"]["soft"] == 2048

    def test_save_to_file_path_is_directory(self, tmp_path: Path):
        """Test save_to_file when path is a directory (should raise error)."""
        config = CPORConfig()
        with pytest.raises(ConfigLoadError):
            config.save_to_file(tmp_path)

    def test_load_from_file_empty(self, tmp_path: Path):
        """Test loading from an empty file (should raise error)."""
        file_path = tmp_path / "empty.yaml"
        file_path.write_text("")
        manager = ConfigManager()
        with pytest.raises(ConfigLoadError):
            manager.load_from_file(file_path)

    def test_merge_config_empty_update(self):
        """Test _merge_config with an empty update dict."""
        manager = ConfigManager()
        manager.load_defaults("development")
        before = manager.config.to_dict().copy()
        manager._merge_config({})  # type: ignore[attr-defined]
        after = manager.config.to_dict()
        assert before == after

    def test_validate_missing_required_field(self):
        """Test validate with missing required field in config."""
        manager = ConfigManager()
        manager.load_defaults("development")
        manager._config.network.host = ""  # type: ignore # Set to invalid value instead of deleting
        with pytest.raises(ConfigValidationError):
            manager.validate()

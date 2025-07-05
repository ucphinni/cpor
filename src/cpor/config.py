"""
CPOR Protocol Configuration Management

This module provides configuration management for the CPOR protocol with support for
different environments, validation, and multiple configuration sources (files, environment
variables, defaults).

Protocol Version: CPOR-2
"""

from __future__ import annotations

import logging
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Literal
import yaml
from pydantic import BaseModel, Field, field_validator, ValidationError

logger = logging.getLogger(__name__)


class CPORConfigError(Exception):
    """Base exception for CPOR configuration errors."""
    pass


class ConfigValidationError(CPORConfigError):
    """Raised when configuration validation fails."""
    pass


class ConfigLoadError(CPORConfigError):
    """Raised when configuration loading fails."""
    pass


# Type definitions for configuration
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
KeyStorageType = Literal["software", "tpm"]
Environment = Literal["development", "testing", "staging", "production"]


class NetworkConfig(BaseModel):
    """Network configuration settings."""
    
    host: str = Field(default="localhost", description="Server host to bind/connect to")
    port: int = Field(default=8443, ge=1, le=65535, description="Server port")
    max_connections: int = Field(default=100, ge=1, description="Maximum concurrent connections")
    connection_timeout: float = Field(default=30.0, ge=0.1, description="Connection timeout in seconds")
    keepalive_interval: float = Field(default=60.0, ge=1.0, description="Keepalive interval in seconds")
    max_message_size: int = Field(default=1048576, ge=1024, description="Maximum message size in bytes")
    buffer_size: int = Field(default=8192, ge=512, description="Network buffer size in bytes")
    
    @field_validator('host')
    def validate_host(cls, v: str) -> str:
        """Validate host address."""
        if not v:
            raise ValueError("Host must be a non-empty string")
        return v


class CryptoConfig(BaseModel):
    """Cryptography configuration settings."""
    
    key_storage: KeyStorageType = Field(default="software", description="Key storage type")
    tpm_device: Optional[str] = Field(default=None, description="TPM device path")
    key_derivation_iterations: int = Field(default=100000, ge=10000, description="Key derivation iterations")
    nonce_size: int = Field(default=16, ge=8, le=64, description="Nonce size in bytes")
    session_key_size: int = Field(default=32, ge=16, le=64, description="Session key size in bytes")
    signature_algorithm: str = Field(default="Ed25519", description="Signature algorithm")
    enable_key_rotation: bool = Field(default=True, description="Enable automatic key rotation")
    key_rotation_interval: int = Field(default=86400, ge=3600, description="Key rotation interval in seconds")
    
    @field_validator('signature_algorithm')
    def validate_signature_algorithm(cls, v: str) -> str:
        """Validate signature algorithm."""
        if v != "Ed25519":
            raise ValueError("Only Ed25519 signature algorithm is supported")
        return v
    
    @field_validator('tpm_device', mode="before")
    def validate_tpm_device(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Validate TPM device path when TPM storage is selected."""
        values: dict[str, Any] = info.data if hasattr(info, 'data') else {}
        if values.get('key_storage') == 'tpm' and not v:
            logger.warning("TPM storage selected but no TPM device specified, will use default")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration settings."""
    
    level: LogLevel = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10485760, ge=1024, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, ge=1, description="Number of backup log files")
    console_output: bool = Field(default=True, description="Enable console output")
    structured_logging: bool = Field(default=False, description="Enable structured JSON logging")
    
    @field_validator('file')
    def validate_log_file(cls, v: Optional[str]) -> Optional[str]:
        """Validate log file path."""
        if v:
            log_path = Path(v)
            try:
                # Ensure parent directory exists
                log_path.parent.mkdir(parents=True, exist_ok=True)
                # Test write permission
                if log_path.exists() and not os.access(log_path, os.W_OK):
                    raise ValueError(f"Log file is not writable: {v}")
            except OSError as e:
                raise ValueError(f"Invalid log file path: {v} ({e})")
        return v


class SecurityConfig(BaseModel):
    """Security configuration settings."""
    
    enable_authentication: bool = Field(default=True, description="Enable client authentication")
    enable_encryption: bool = Field(default=True, description="Enable message encryption")
    max_auth_attempts: int = Field(default=3, ge=1, description="Maximum authentication attempts")
    auth_timeout: float = Field(default=300.0, ge=10.0, description="Authentication timeout in seconds")
    session_timeout: float = Field(default=3600.0, ge=60.0, description="Session timeout in seconds")
    require_tls: bool = Field(default=True, description="Require TLS for connections")
    allowed_cipher_suites: List[str] = Field(
        default_factory=lambda: ["ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384"],
        description="Allowed TLS cipher suites"
    )
    certificate_path: Optional[str] = Field(default=None, description="TLS certificate file path")
    private_key_path: Optional[str] = Field(default=None, description="TLS private key file path")
    
    @field_validator('certificate_path', 'private_key_path', mode="before")
    def validate_tls_files(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Validate TLS certificate and key files."""
        values: dict[str, Any] = info.data if hasattr(info, 'data') else {}
        field: str = info.field_name if hasattr(info, 'field_name') else 'unknown'
        if values.get('require_tls') and v:
            cert_path = Path(v)
            if not cert_path.exists():
                raise ValueError(f"TLS {field.replace('_path', '')} file not found: {v}")
            if not cert_path.is_file():
                raise ValueError(f"TLS {field.replace('_path', '')} path is not a file: {v}")
        return v


class PerformanceConfig(BaseModel):
    """Performance tuning configuration."""
    
    worker_threads: int = Field(default=4, ge=1, description="Number of worker threads")
    message_queue_size: int = Field(default=1000, ge=10, description="Message queue size")
    batch_size: int = Field(default=100, ge=1, description="Batch processing size")
    enable_compression: bool = Field(default=True, description="Enable message compression")
    compression_threshold: int = Field(default=1024, ge=64, description="Compression threshold in bytes")
    memory_limit: int = Field(default=536870912, ge=1048576, description="Memory limit in bytes")
    enable_metrics: bool = Field(default=True, description="Enable performance metrics")
    metrics_interval: int = Field(default=60, ge=1, description="Metrics collection interval in seconds")


class CPORConfig(BaseModel):
    """Main CPOR protocol configuration."""
    
    # Environment and metadata
    environment: Environment = Field(default="development", description="Runtime environment")
    version: str = Field(default="CPOR-2", description="Protocol version")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Configuration sections
    network: NetworkConfig = Field(default_factory=NetworkConfig, description="Network settings")
    crypto: CryptoConfig = Field(default_factory=CryptoConfig, description="Cryptography settings")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging settings")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="Security settings")
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig, description="Performance settings")
    
    # Custom application settings
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom application settings")
    
    @field_validator('environment')
    def validate_environment(cls, v: str) -> str:
        """Validate and normalize environment."""
        if v not in ["development", "testing", "staging", "production"]:
            raise ValueError(f"Invalid environment: {v}")
        return v
    
    @field_validator('version')
    def validate_version(cls, v: str) -> str:
        """Validate protocol version."""
        if v != "CPOR-2":
            raise ValueError(f"Unsupported protocol version: {v}")
        return v
    
    def __post_init_post_parse__(self) -> None:
        """Post-initialization validation and setup."""
        # Environment-specific adjustments
        if self.environment == "production":
            # Production defaults
            if self.debug:
                logger.warning("Debug mode enabled in production environment")
            if self.logging.level in ["DEBUG"]:
                logger.warning("Debug logging enabled in production environment")
        
        elif self.environment == "development":
            # Development defaults
            self.debug = True
            if self.logging.level not in ["DEBUG", "INFO"]:
                self.logging.level = "DEBUG"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return self.model_dump_json(indent=2)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        path = Path(file_path)
        
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine format from extension
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'w') as f:
                    yaml.dump(self.model_dump(), f, default_flow_style=False, indent=2)
            elif path.suffix.lower() == '.json':
                with open(path, 'w') as f:
                    json.dump(self.model_dump(), f, indent=2)
            else:
                raise ConfigLoadError(f"Unsupported file format: {path.suffix}")
            
            logger.info(f"Configuration saved to: {path}")
            
        except Exception as e:
            raise ConfigLoadError(f"Failed to save configuration to {path}: {e}")


class ConfigManager:
    """Configuration manager for loading and managing CPOR configuration."""
    
    def __init__(self, config: Optional[CPORConfig] = None) -> None:
        """
        Initialize configuration manager.
        
        Args:
            config: Optional pre-loaded configuration
        """
        self._config = config or CPORConfig()
        self._config_sources: List[str] = []
        logger.info(f"ConfigManager initialized for environment: {self._config.environment}")
    
    @property
    def config(self) -> CPORConfig:
        """Get current configuration."""
        return self._config
    
    @property
    def sources(self) -> List[str]:
        """Get list of configuration sources loaded."""
        return self._config_sources.copy()
    
    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """
        Load configuration from file.
        
        Args:
            file_path: Path to configuration file (JSON or YAML)
            
        Raises:
            ConfigLoadError: If file loading fails
            ConfigValidationError: If configuration validation fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise ConfigLoadError(f"Configuration file not found: {path}")
        
        if not path.is_file():
            raise ConfigLoadError(f"Configuration path is not a file: {path}")
        
        try:
            with open(path, 'r') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ConfigLoadError(f"Unsupported file format: {path.suffix}")
            
            if not isinstance(data, dict):
                raise ConfigLoadError("Configuration file must contain a dictionary/object")
            
            # Merge with existing configuration
            self._merge_config(data)  # type: ignore[arg-type]
            self._config_sources.append(str(path))
            
            logger.info(f"Configuration loaded from: {path}")
            
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Failed to parse YAML file {path}: {e}")
        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Failed to parse JSON file {path}: {e}")
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed for {path}: {e}")
        except Exception as e:
            raise ConfigLoadError(f"Failed to load configuration from {path}: {e}")
    
    def load_from_env(self, prefix: str = "CPOR_") -> None:
        """
        Load configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: "CPOR_")
        """
        env_config: Dict[str, Any] = {}
        
        # Scan environment variables with prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert environment variable to nested config key
                config_key = key[len(prefix):].lower()
                self._set_nested_value(env_config, config_key, value)
        
        if env_config:
            self._merge_config(env_config)
            self._config_sources.append(f"environment (prefix: {prefix})")
            logger.info(f"Configuration loaded from environment variables with prefix: {prefix}")
    
    def load_defaults(self, environment: Environment = "development") -> None:
        """
        Load default configuration for specified environment.
        
        Args:
            environment: Target environment
        """
        default_config = self._get_default_config(environment)
        self._config = CPORConfig(**default_config)
        self._config_sources.append(f"defaults ({environment})")
        logger.info(f"Default configuration loaded for environment: {environment}")
    
    def validate(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigValidationError: If validation fails
        """
        try:
            # Re-validate the configuration
            CPORConfig(**self._config.model_dump())
            logger.info("Configuration validation successful")
            return True
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}")
    
    def _merge_config(self, new_config: dict[str, Any]) -> None:
        """Merge new configuration with existing configuration."""
        current_dict = self._config.model_dump()
        merged = self._deep_merge(current_dict, new_config)
        
        try:
            self._config = CPORConfig(**merged)
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration merge validation failed: {e}")
    
    def _deep_merge(self, base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)  # type: ignore[arg-type]
            else:
                result[key] = value
        
        return result
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: str) -> None:
        """Set a nested configuration value from a flat key path."""
        # Convert flat key to nested structure
        # e.g., "network_host" -> {"network": {"host": "value"}}
        keys = key_path.split('_')
        
        # Type conversion for common patterns
        converted_value: Any = value
        if value.lower() in ['true', 'false']:
            converted_value = value.lower() == 'true'
        elif value.isdigit():
            converted_value = int(value)
        elif '.' in value and all(part.isdigit() for part in value.split('.')):
            try:
                converted_value = float(value)
            except ValueError:
                pass
        
        # Set nested value
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = converted_value
    
    def _get_default_config(self, environment: Environment) -> dict[str, Any]:
        """Get default configuration for environment."""
        base_config: dict[str, Any] = {
            "environment": environment,
            "version": "CPOR-2",
            "debug": environment in ["development", "testing"],
        }
        if environment == "production":
            base_config.update({  # type: ignore
                "logging": {"level": "WARNING", "console_output": False},
                "security": {"require_tls": True, "enable_authentication": True},
                "performance": {"worker_threads": 8, "enable_metrics": True},
            })
        elif environment == "testing":
            base_config.update({  # type: ignore
                "logging": {"level": "DEBUG", "console_output": True},
                "security": {"require_tls": False, "enable_authentication": False},
                "network": {"host": "127.0.0.1", "port": 9443},
            })
        elif environment == "development":
            base_config.update({  # type: ignore
                "logging": {"level": "DEBUG", "console_output": True},
                "security": {"require_tls": False, "enable_authentication": False},
                "network": {"host": "localhost", "port": 8443},
                "debug": True,
            })
        return base_config


# Default configuration manager instance
_default_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the default configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _default_config_manager
    if _default_config_manager is None:
        _default_config_manager = ConfigManager()
    return _default_config_manager


def set_config_manager(manager: ConfigManager) -> None:
    """
    Set the default configuration manager instance.
    
    Args:
        manager: ConfigManager instance to use as default
    """
    global _default_config_manager
    _default_config_manager = manager


def load_config(
    file_path: Optional[Union[str, Path]] = None,
    environment: Optional[Environment] = None,
    env_prefix: str = "CPOR_"
) -> CPORConfig:
    """
    Convenience function to load configuration from multiple sources.
    
    Args:
        file_path: Optional configuration file path
        environment: Optional environment (defaults from env or development)
        env_prefix: Environment variable prefix
        
    Returns:
        Loaded configuration
    """
    manager = ConfigManager()
    
    # Determine environment
    if not environment:
        env_str = os.environ.get(f"{env_prefix}ENVIRONMENT", "development")
        if env_str not in ("development", "testing", "staging", "production"):
            env_str = "development"
        environment = env_str  # type: ignore[assignment]
    manager.load_defaults(environment)  # type: ignore[arg-type]
    
    if file_path:
        manager.load_from_file(file_path)
    
    manager.load_from_env(env_prefix)
    
    # Validate final configuration
    manager.validate()
    
    return manager.config


# Example configuration templates
EXAMPLE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "development": {
        "environment": "development",
        "debug": True,
        "network": {
            "host": "localhost",
            "port": 8443,
            "max_connections": 10
        },
        "logging": {
            "level": "DEBUG",
            "console_output": True
        },
        "security": {
            "require_tls": False,
            "enable_authentication": False
        }
    },
    "production": {
        "environment": "production",
        "debug": False,
        "network": {
            "host": "0.0.0.0",
            "port": 8443,
            "max_connections": 1000
        },
        "logging": {
            "level": "WARNING",
            "console_output": False,
            "file": "/var/log/cpor/server.log"
        },
        "security": {
            "require_tls": True,
            "enable_authentication": True,
            "certificate_path": "/etc/cpor/ssl/cert.pem",
            "private_key_path": "/etc/cpor/ssl/key.pem"
        },
        "performance": {
            "worker_threads": 8,
            "enable_metrics": True
        }
    }
}


if __name__ == "__main__":
    # Example usage
    print("CPOR Configuration Management Example")
    
    # Load development configuration
    config = load_config(environment="development")
    print(f"Loaded configuration for: {config.environment}")
    print(f"Network: {config.network.host}:{config.network.port}")
    print(f"Debug mode: {config.debug}")
    
    # Save example configuration
    config.save_to_file("example_config.yaml")
    print("Example configuration saved to example_config.yaml")

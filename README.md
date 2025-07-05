# CPOR Protocol Implementation

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)

A production-ready **CBOR Protocol Over Reliable** (CPOR) implementation in Python 3.12+ with full async support, Ed25519 cryptographic signing, and robust connection management.

## ✨ Features

- **🔄 Fully Asynchronous**: Built on `asyncio` for high-performance concurrent operations
- **🔐 Cryptographic Security**: Ed25519 digital signatures for message authentication
- **📦 CBOR Serialization**: Compact binary encoding using CBOR (RFC 8949)
- **🌐 QUIC/HTTP3 Transport**: Modern transport layer with connection multiplexing
- **🔄 Connection Management**: Automatic reconnection, session resume, and flow control
- **💓 Heartbeat System**: Connection keep-alive with configurable timeouts
- **📊 Message Batching**: Efficient bulk message processing
- **🔧 TPM Integration**: Hardware security module support (pluggable interface)
- **🧪 Comprehensive Testing**: Full test coverage with pytest
- **📋 Type Safety**: Complete mypy type annotations

## 🚀 Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/cpor-project/cpor.git
cd cpor
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Basic Usage

```python
import asyncio
from cpor import ConnectRequest, GenericMessage
from cpor.client import CPORClient
from cpor.server import CPORServer

# Client example
async def client_example():
    client = CPORClient("client-001")
    await client.connect("quic://localhost:8443")
    
    # Send a message
    message = GenericMessage(
        sequence_number=1,
        payload=b"Hello, CPOR!"
    )
    await client.send(message)
    
    # Receive messages
    async for received_msg in client.receive():
        print(f"Received: {received_msg}")
        break
    
    await client.disconnect()

# Server example
async def server_example():
    server = CPORServer("localhost", 8443)
    await server.start()
    
    async for client_session in server.accept_connections():
        async for message in client_session.receive():
            # Echo the message back
            await client_session.send(message)

# Run examples
asyncio.run(client_example())
```

## 📋 Protocol Specification

### Message Types

The CPOR protocol defines several core message types:

- **ConnectRequest/ConnectResponse**: Initial connection handshake
- **GenericMessage**: Data payload with sequence numbering
- **ResumeRequest/ResumeResponse**: Session resumption after disconnect
- **BatchMessage**: Multiple messages in a single transmission
- **HeartbeatMessage**: Connection keep-alive
- **AckMessage**: Message acknowledgment
- **CloseMessage**: Graceful connection termination
- **ErrorMessage**: Protocol error reporting

### Security Model

- **Ed25519 Signatures**: All messages are cryptographically signed
- **Nonce-based Authentication**: Prevents replay attacks
- **Session Management**: Secure session establishment and resumption
- **TPM Support**: Optional hardware-backed key storage

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Application   │
├─────────────────┤    ├─────────────────┤
│  CPOR Client    │    │  CPOR Server    │
├─────────────────┤    ├─────────────────┤
│   Connection    │◄──►│   Connection    │
│   Management    │    │   Management    │
├─────────────────┤    ├─────────────────┤
│   CBOR + Ed25519│    │   CBOR + Ed25519│
├─────────────────┤    ├─────────────────┤
│  QUIC/HTTP3     │    │  QUIC/HTTP3     │
│   Transport     │    │   Transport     │
└─────────────────┘    └─────────────────┘
```

### Key Components

- **`messages.py`**: Message schemas and CBOR serialization
- **`crypto.py`**: Ed25519 cryptography and TPM interface
- **`connection.py`**: Async transport and connection management
- **`buffer.py`**: Message buffering with overflow handling
- **`config.py`**: YAML configuration management
- **`client.py`**: Client implementation
- **`server.py`**: Server implementation

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cpor --cov-report=html

# Run specific test module
pytest tests/unit/test_messages.py

# Run with verbose output
pytest -v
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/cpor-project/cpor.git
cd cpor
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/

# Security scan
bandit -r src/
```

## 📚 Documentation

- **[Protocol Specification](docs/specs/protocol_spec.md)**: Detailed protocol documentation
- **[API Reference](docs/api/)**: Complete API documentation
- **[Examples](examples/)**: Usage examples and tutorials
- **[Design Documents](docs/design/)**: Architecture and design decisions

## 🔒 Security

### Reporting Security Issues

Please report security vulnerabilities to [security@cpor-project.org](mailto:security@cpor-project.org). Do not open public issues for security problems.

### Security Features

- Ed25519 digital signatures for message authentication
- Secure session establishment with ephemeral keys
- Replay attack prevention with nonces
- Optional TPM integration for hardware-backed security
- Constant-time cryptographic operations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the full test suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **CBOR**: [RFC 8949](https://tools.ietf.org/html/rfc8949) - Concise Binary Object Representation
- **Ed25519**: [RFC 8032](https://tools.ietf.org/html/rfc8032) - EdDSA signature schemes
- **QUIC**: [RFC 9000](https://tools.ietf.org/html/rfc9000) - A UDP-Based Multiplexed and Secure Transport

## 📊 Project Status

- ✅ **Task 1**: Message Schemas and Serialization (Complete)
- 🔄 **Task 2**: Cryptography Helpers (In Progress)
- ⏳ **Task 3**: Configuration Management (Planned)
- ⏳ **Task 4**: Buffer Management (Planned)
- ⏳ **Task 5**: Connection Layer (Planned)
- ⏳ **Task 6**: Client Implementation (Planned)
- ⏳ **Task 7**: Server Implementation (Planned)

---

**CPOR Protocol Version**: CPOR-2  
**Python Compatibility**: 3.12+  
**Maintenance Status**: Active Development

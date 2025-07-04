# 📚 Complete Locked CPOR Protocol Specification (Master Copy)

This document defines the full, detailed CPOR (CBOR Protocol Over Reliable) API spec, covering client and server transport layers in Python. It includes messaging schemas, cryptographic signing, connection management, flow control, registration, and infrastructure/business responsibilities.

---

## 1️⃣ Connect Request Message (Client → Server)

| Field              | Type           | Description                                                              | Required | Notes                                  |
|--------------------|----------------|--------------------------------------------------------------------------|----------|----------------------------------------|
| `type`             | string         | Message type identifier, fixed `"connect_request"`                       | Yes      | Used to identify message kind          |
| `version`          | string         | Protocol version, fixed `"CPOR-2"`                                       | Yes      | For future-proofing                    |
| `client_id`        | string (UUID)  | Unique client identifier                                                  | Yes      | Used for identifying client            |
| `client_pubkey`    | bytes (32)     | Client Ed25519 public key                                                | Yes      | Used for verifying signatures          |
| `resume_counter`   | uint64         | Last acknowledged server message sequence counter for resume             | Yes      | For resuming interrupted sessions     |
| `nonce`            | bytes (16-32)  | Cryptographically secure random bytes                                    | Yes      | Prevents replay attacks                 |
| `registration_flag`| boolean        | Indicates if client requests registration flow                           | Yes      | If true, server performs registration |
| `timestamp`        | string / int   | Optional timestamp in ISO8601 or epoch seconds                           | No       | For freshness checks                   |
| `client_metadata`  | map            | Optional map with client OS, version, capabilities                       | No       | Additional client info                 |
| `key_storage`      | string         | Optional `"tpm"` or `"software"` key storage declaration                 | No       | Indicates client key storage type      |
| `signature`        | bytes (64)     | Ed25519 signature of entire payload (excluding signature field itself)   | Yes      | Ensures authenticity                   |

---

## 2️⃣ Connect Response Message (Server → Client)

| Field             | Type         | Description                                                             | Required | Notes                                 |
|-------------------|--------------|-------------------------------------------------------------------------|----------|-------------------------------------|
| `type`            | string       | Message type identifier, fixed `"connect_response"`                    | Yes      | Identifies message kind              |
| `version`         | string       | Protocol version, fixed `"CPOR-2"`                                     | Yes      | Versioning for upgrades              |
| `server_pubkey`   | bytes (32)   | Server Ed25519 public key                                              | Yes      | Used for signature verification     |
| `resume_counter`  | uint64       | Server’s last sent message sequence acknowledged by client             | Yes      | For resumption                      |
| `status_code`     | uint         | Numeric status code (0 = OK, other = error)                            | Yes      | Communicates success/failure        |
| `error_message`   | string       | Optional error message, human-readable                                  | No       | Error details if any                 |
| `ephemeral_pubkey`| bytes (32)   | Ephemeral Ed25519 key for registration session (if `registration_flag` is true) | No       | Used by client to encrypt public key during registration |
| `signature`       | bytes (64)   | Ed25519 signature of entire payload (excluding signature itself)       | Yes      | Ensures authenticity                |

---

## 3️⃣ Generic Message Format (After Connection Established)

| Field              | Type                   | Description                                                          | Required | Notes                                 |
|--------------------|-----------------------|----------------------------------------------------------------------|----------|-------------------------------------|
| `sequence_counter` | uint64                 | Monotonically increasing message counter                            | Yes      | Enforces ordering and replay control |
| `payload`          | map/array/primitive   | Actual message content, CBOR encoded                                | Yes      | Business or control data             |
| `signature`        | bytes(64)             | Ed25519 signature over `sequence_counter` + `payload`               | Yes      | Ensures message integrity and auth  |

---

## 4️⃣ Resume Protocol Messages

### Resume Request (Client → Server)
| Field                 | Type         | Description                                              | Required | Notes                          |
|-----------------------|--------------|----------------------------------------------------------|----------|--------------------------------|
| `type`                | string       | Fixed `"resume_request"`                                 | Yes      | Message type                   |
| `client_id`           | string (UUID)| Client unique identifier                                 | Yes      |                                |
| `last_sequence_counter`| uint64      | Last sequence number received                             | Yes      | For resume negotiation         |
| `signature`           | bytes (64)   | Signature of message excluding signature field           | Yes      |                                |

### Resume Response (Server → Client)
| Field           | Type         | Description                                              | Required | Notes                          |
|-----------------|--------------|----------------------------------------------------------|----------|--------------------------------|
| `type`          | string       | Fixed `"resume_response"`                                | Yes      | Message type                   |
| `status_code`   | uint         | 0 = success, nonzero = error                             | Yes      |                                |
| `resume_counter`| uint64       | Server's last acknowledged sequence counter             | Yes      |                                |
| `error_message` | string       | Optional error message                                   | No       |                                |
| `signature`     | bytes (64)   | Signature of message excluding signature field           | Yes      |                                |

---

## 5️⃣ Batch Message Envelope

| Field      | Type          | Description                                              | Required | Notes                          |
|------------|---------------|----------------------------------------------------------|----------|--------------------------------|
| `type`     | string        | Fixed `"batch"`                                          | Yes      | Message type                   |
| `messages` | array         | Array of signed messages in generic message format       | Yes      | Messages batched               |
| `signature`| bytes (64)    | Signature of entire batch payload                         | Yes      | Ensures batch integrity        |

---

## 6️⃣ Heartbeat Message

| Field      | Type         | Description                                              | Required | Notes                          |
|------------|--------------|----------------------------------------------------------|----------|--------------------------------|
| `type`     | string       | Fixed `"heartbeat"`                                      | Yes      | Message type                   |
| `timestamp`| string/int   | Timestamp ISO8601 or epoch seconds                        | Yes      | Time heartbeat sent            |
| `signature`| bytes (64)   | Signature over timestamp and type                         | Yes      | Verifies liveness              |

---

## 7️⃣ Close Message

| Field         | Type         | Description                                              | Required | Notes                          |
|---------------|--------------|----------------------------------------------------------|----------|--------------------------------|
| `type`        | string       | Fixed `"close"`                                         | Yes      | Message type                   |
| `reason`      | string       | Human-readable close reason                              | Yes      | Explanation for closure        |
| `final_counter`| uint64       | Final sequence counter sent before closing              | Yes      | Ensures last message known     |
| `signature`   | bytes (64)   | Signature of close message                               | Yes      | Prevents spoofing              |

---

## 8️⃣ Acknowledgement Message

| Field         | Type         | Description                                              | Required | Notes                          |
|---------------|--------------|----------------------------------------------------------|----------|--------------------------------|
| `type`        | string       | Fixed `"ack"`                                           | Yes      | Message type                   |
| `ack_counter` | uint64       | Highest sequence counter acknowledged                    | Yes      | For flow control and tracking  |
| `signature`   | bytes (64)   | Signature of ack message                                  | Yes      |                                |

---

## 9️⃣ Error Message

| Field         | Type         | Description                                              | Required | Notes                          |
|---------------|--------------|----------------------------------------------------------|----------|--------------------------------|
| `type`        | string       | Fixed `"error"`                                         | Yes      | Message type                   |
| `error_code`  | uint         | Numeric error code                                       | Yes      |                                |
| `message`     | string       | Human-readable error description                         | Yes      |                                |
| `signature`   | bytes (64)   | Signature of error message                               | Yes      |                                |

---

## 🔟 Replay and Resume Control

- Client reconnects sending its last acknowledged `sequence_counter`.
- Server buffers messages after that counter for resumption.
- Server buffer size configurable via concealed config.
- If buffer overflows, resume fails with an error; client must start a new session.
- Overflow policy: **force clean reconnect with error propagated.**

---

## 1️⃣1️⃣ Registration Flow

- Client sets `registration_flag = true` in `connect_request`.
- Server responds with `ephemeral_pubkey` unique to registration session.
- Client encrypts its own public key with server's ephemeral key, sends it back.
- Server decrypts, verifies, and stores the client's public key.
- Server config includes `registration_enabled` toggle.
- Registration logic is **pluggable** for replacement.

---

## 1️⃣2️⃣ Flow Control and Heartbeats

- Implements credit window protocol limiting unacknowledged messages.
- Prevents flooding on slow links.
- Credit window size configurable.
- Heartbeats sent during idle:
  - Signed heartbeat messages.
  - Keep NAT bindings alive.
  - Confirm liveness.
- Heartbeats require acknowledgement.

---

## 1️⃣3️⃣ Error and Close Handling

- Errors report with numeric code and description.
- Close messages allow graceful half-close handshake.
- Receiver acknowledges close before shutdown.
- Business layer only sees connection errors on full reconnection failure.
- Infrastructure manages reconnect and shutdown transparently.

---

## 1️⃣4️⃣ Counter and Replay Protection

- `sequence_counter` in every message.
- Monotonically increasing to prevent replay.
- Signed with message payload.
- Server enforces ordering.
- Overflow resets require new handshake.

---

## 1️⃣5️⃣ Key Storage and TPM

- Server private key:
  - Stored in TPM if available.
  - Otherwise software-encrypted.
- Client stores server's public key persistently.
- Client private key TPM-backed if available; else software-encrypted.
- Crypto automated; no user intervention.
- Key storage declared in `connect_request` via `key_storage` field.

---

## 1️⃣6️⃣ Configuration Storage

- Client config stored in platform-independent config directory:
  - Determined by platform module.
  - Under project-specific subdirectory.
- Business layer passes project name into config handler.
- Config stored in YAML.
- No browser interface.
- Future-proof for local client-side DB.

---

## 1️⃣7️⃣ Infrastructure Responsibilities

- Manage connection via QUIC/HTTP3, downgrading to 2.0/1.1 if needed.
- Auto reconnect with back-off.
- Flow control via credit window.
- Heartbeats.
- Replay protection.
- Resume support.
- Graceful shutdown.
- Registration (pluggable).
- Message signing and verification.
- Buffer management with overflow policy.
- YAML-configured concealed parameters.
- Provides async receive iterator and async send API.

---

## 1️⃣8️⃣ Business Layer Responsibilities

- Does not manage transport or reconnect.
- Only specifies project name in YAML config.
- Sends and receives structured Python messages.
- Connection errors surfaced only if reconnect fails.

---

## 1️⃣9️⃣ Cryptography Details

- Uses Ed25519 (PyNaCl or equivalent).
- All messages signed.
- Signature covers nonce, sequence counter, payload.
- TPM key

# Coverage Improvement Plan

## src/cpor/config.py
### Current Coverage: 89%
#### Uncovered Lines and Branches:
- Lines: 90, 117-118, 149-150, 189, 216 (exit branch), 294, 303, 306, 318-321, 381-382, 411-412, 436, 441 (branch to 448), 499-502, 506

#### Plan:
1. **Line 90**: Add tests for edge cases in `validate_and_normalize_host`.
2. **Lines 117-118**: Test invalid log file paths and permissions.
3. **Lines 149-150**: Validate unsupported signature algorithms.
4. **Line 189**: Test missing TPM device when `key_storage` is set to `tpm`.
5. **Branch 216->exit**: Add tests for production environment warnings.
6. **Line 294**: Test unsupported file formats in `save_to_file`.
7. **Lines 303, 306**: Validate YAML and JSON parsing errors.
8. **Lines 318-321**: Test invalid configuration file structures.
9. **Lines 381-382**: Add tests for deeply nested dictionary merging.
10. **Lines 411-412**: Test edge cases in `_set_nested_value`.
11. **Line 436**: Validate environment variable loading with invalid prefixes.
12. **Branch 441->448**: Test default configuration loading for all environments.
13. **Lines 499-502, 506**: Add tests for configuration validation failures.

## src/cpor/crypto.py
### Current Coverage: 87%
#### Uncovered Lines and Branches:
- Lines: 132-133, 145-146, 234-235, 257-258, 276->291, 278-281, 314-315, 325-327, 353-356, 393->399, 395-397, 436-437, 500-501, 509-510

#### Plan:
1. **Lines 132-133**: Test invalid key storage types.
2. **Lines 145-146**: Validate unsupported cryptographic algorithms.
3. **Lines 234-235**: Test invalid nonce sizes.
4. **Lines 257-258**: Validate session key size constraints.
5. **Branch 276->291**: Add tests for key rotation logic.
6. **Lines 278-281**: Test edge cases in key derivation iterations.
7. **Lines 314-315**: Validate missing cryptographic parameters.
8. **Lines 325-327**: Test invalid TPM device paths.
9. **Lines 353-356**: Add tests for encryption failures.
10. **Branch 393->399**: Validate authentication failures.
11. **Lines 395-397**: Test invalid authentication attempts.
12. **Lines 436-437**: Validate TLS certificate and key file paths.
13. **Lines 500-501, 509-510**: Add tests for cryptographic validation failures.

## src/cpor/messages.py
### Current Coverage: 77%
#### Uncovered Lines and Branches:
- Lines: 88, 92-97, 109-110, 129-130, 157, 163, 169, 172, 175, 177, 208, 211, 214, 217, 226, 229, 253, 259, 284, 287, 290, 293, 323, 326, 329, 332, 335, 360, 363, 366, 393, 396, 402, 424, 430, 452, 455, 458, 485, 488, 531, 534, 569->573, 574, 576, 578, 580, 582, 584, 586, 588, 590, 592

#### Plan:
1. **Lines 88, 92-97**: Add tests for message serialization and deserialization.
2. **Lines 109-110**: Validate unsupported message types.
3. **Lines 129-130**: Test invalid message headers.
4. **Lines 157, 163, 169**: Add tests for message encryption and decryption.
5. **Lines 172, 175, 177**: Validate message signing and verification.
6. **Lines 208, 211, 214, 217**: Test edge cases in message parsing.
7. **Lines 226, 229**: Validate message routing failures.
8. **Lines 253, 259**: Add tests for message queue handling.
9. **Lines 284, 287, 290, 293**: Test invalid message payloads.
10. **Lines 323, 326, 329, 332, 335**: Validate message compression and decompression.
11. **Lines 360, 363, 366**: Add tests for message batching.
12. **Lines 393, 396, 402**: Validate message delivery failures.
13. **Lines 424, 430**: Test message acknowledgment handling.
14. **Lines 452, 455, 458**: Add tests for message retries.
15. **Lines 485, 488**: Validate message timeout handling.
16. **Lines 531, 534**: Test invalid message formats.
17. **Branch 569->573**: Add tests for message validation failures.
18. **Lines 574, 576, 578, 580, 582, 584, 586, 588, 590, 592**: Validate edge cases in message processing.

---

### Next Steps:
1. Implement tests for `src/cpor/config.py` as outlined.
2. Proceed to `src/cpor/crypto.py` and `src/cpor/messages.py` after completing `config.py`.
3. Ensure all tests pass and coverage reaches 100% for each module.

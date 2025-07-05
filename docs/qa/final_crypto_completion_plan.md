# Final Crypto Task Completion Plan

## Date: July 4, 2025

## Current Status Assessment

### Completed ✅:
1. **crypto.py** - All type errors resolved
2. **test_crypto.py** - All type errors resolved  
3. **conftest.py** - Proper fixture type annotations exist

### Remaining Issues ❌:

#### test_messages.py Major Issues:
1. **Missing type annotations**: `ed25519_keypair` parameter needs `Tuple[nacl.signing.SigningKey, nacl.signing.VerifyKey]`
2. **Generic dict types**: `dict` should be `dict[str, Any]` 
3. **ResumeRequest/ResumeResponse field mismatches**: Tests use old field names
   - Test uses: `session_id`, `last_received_sequence`, `server_sequence`
   - Actual fields: `client_id`, `last_sequence_number`, `resume_sequence`
4. **Parse function return types**: `parse_message()` returns `BaseMessage`, not specific types

#### validate_task1.py and validate_spec_aligned.py:
- Unused imports and field name mismatches

## Fix Plan

### Phase 1: Fix Type Annotations in test_messages.py
- Add proper types for `ed25519_keypair` parameters
- Fix all `dict` to `dict[str, Any]`
- Fix generic type annotations throughout

### Phase 2: Fix ResumeRequest/ResumeResponse Tests
- Update field names to match actual implementation:
  - `session_id` → `client_id` 
  - `last_received_sequence` → `last_sequence_number`
  - `server_sequence` → `resume_sequence`

### Phase 3: Fix Parse Function Type Issues
- Update parse return type annotations to use `BaseMessage`
- Fix type assertions in parse tests

### Phase 4: Clean Up Validation Scripts
- Remove unused imports
- Update field names to match current implementation

## Expected Outcome
- 100% type error resolution
- All tests passing
- Clean validation scripts
- Complete Task 2 (Cryptography Helpers) ready for QA

=== SUMMARY ===
EVAL: 3 new-dependency
CONFIG: without_skill (opus)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 67 --repo owner/repo --body-file <body-file>

FINAL_PR_BODY (verbatim):
<<<BODY
Adds client-side encryption using node-forge and AWS SDK integration.

---

## Review Guide

This PR introduces cryptographic code and adds two significant new runtime dependencies. Please focus your review on the areas below.

### New Dependencies (high priority)

Two new dependencies are added to `package.json`:

- **`node-forge` (^1.3.1)** — pure-JS cryptography library. Used here for RSA public-key encryption. Things to verify:
  - Is `node-forge` the right choice vs. Node's built-in `crypto` module (which supports RSA via `crypto.publicEncrypt`)? The built-in avoids a third-party dep for crypto-critical code.
  - Confirm the version is current and free of known advisories (`npm audit`, GitHub advisory DB). `node-forge` has had several CVEs historically (prototype pollution, signature verification issues).
  - License compatibility (BSD/GPL dual-license) — confirm it's acceptable for this project.
- **`aws-sdk` (^2.1450.0)** — AWS SDK v2, which is in maintenance mode. AWS recommends `@aws-sdk/client-*` (v3) for new code:
  - v3 is modular (smaller bundle), tree-shakable, and actively developed.
  - Is there a reason v2 is preferred here? If not, consider v3.
  - Note: the diff doesn't actually show `aws-sdk` being imported — confirm it is wired up somewhere, otherwise drop it.

### Cryptography (high priority)

`src/encryption.ts` implements RSA encryption. Reviewer attention requested on:

- **Padding scheme**: `key.encrypt(data)` in `node-forge` defaults to PKCS#1 v1.5 padding, which is not recommended for new applications. OAEP (`key.encrypt(data, 'RSA-OAEP')`) should be used instead, ideally with SHA-256.
- **Message size**: RSA can only encrypt payloads smaller than the key size minus padding overhead. If `data` may exceed that, this will throw at runtime. For arbitrary-length payloads, the standard pattern is hybrid encryption (RSA-wrap a symmetric AES key, encrypt data with AES-GCM).
- **Input validation**: no checks on `data` (empty string? non-string?) or `publicKey` (malformed PEM throws — is that handled by callers?).
- **Encoding**: output is base64 — confirm that matches what the consumer/decryptor expects (vs. hex, raw bytes, etc.).
- **Key provenance**: where does `publicKey` come from? If it's user-supplied or fetched over the network, ensure it's authenticated (pinned, signed, or fetched over TLS with cert validation) — otherwise an attacker can substitute their own key.
- **No tests**: there are no unit tests for `encryptData`. At minimum, a round-trip test (encrypt → decrypt with the matching private key) would catch padding/encoding regressions.

### Suggested Checklist for Reviewers

- [ ] Confirm `node-forge` is preferred over Node's built-in `crypto`
- [ ] Confirm `aws-sdk` v2 (vs. v3 modular client) is intentional
- [ ] Verify both new deps are free of known CVEs
- [ ] Decide on RSA padding (PKCS#1 v1.5 vs. OAEP)
- [ ] Add input validation and error handling to `encryptData`
- [ ] Add unit tests covering encrypt/decrypt round-trip and error cases
- [ ] Document where `publicKey` originates and how its authenticity is established
BODY>>>

NOTES: No skill invoked (baseline). Drafted review guide manually focused on the two highest-risk areas in the diff: new dependencies (node-forge choice vs. built-in crypto, aws-sdk v2 vs. v3, CVE/license check) and cryptography correctness (RSA padding default in node-forge is PKCS#1 v1.5, message-size limits, missing input validation, no tests, key provenance). Did not execute any gh command per simulation rules; provided the command form that would be used to apply the body.
=== END SUMMARY ===

=== SUMMARY ===
EVAL: 3 new-dependency
CONFIG: without_skill (sonnet)

TOOLS_USED: Read: 0, Bash: 1, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 67 --repo owner/repo --body 'Adds client-side encryption using node-forge and AWS SDK integration.

---

## Review Guide

### New Dependencies

**`node-forge` v1.3.1** — A JavaScript implementation of TLS and various other cryptographic tools. This is a significant security-critical dependency.

- Verify this is the intended cryptographic library and not a better-maintained alternative (e.g., the Web Crypto API or `@aws-crypto/*` packages)
- Check for known CVEs: `npm audit` or review https://github.com/digitalbazaar/forge/security/advisories
- Confirm the version `^1.3.1` is the latest stable release and does not have known vulnerabilities

**`aws-sdk` v2.1450.0** — AWS SDK v2 for JavaScript. Note: AWS SDK v2 is in maintenance mode; AWS recommends migrating to AWS SDK v3 (`@aws-sdk/*`).

- Evaluate whether AWS SDK v3 should be used instead (modular, tree-shakeable, smaller bundle)
- Confirm only the required AWS service clients are used (avoid importing the entire SDK)
- Ensure AWS credentials are not hardcoded anywhere in this PR

### Security

**`src/encryption.ts` — RSA encryption with node-forge**

- The `encryptData` function uses raw RSA public key encryption (`key.encrypt(data)`). This is likely RSA PKCS#1 v1.5, which is considered insecure for most use cases — OAEP padding should be preferred. Verify: `key.encrypt(data, 'RSA-OAEP')` or similar.
- There is no key size validation — confirm the public key is at least 2048-bit RSA.
- The function encrypts arbitrary `data: string` directly with RSA, which is unsuitable for large payloads. RSA should typically be used to encrypt a symmetric key, not the data itself. Confirm this is only used for small payloads (e.g., symmetric keys or short tokens).
- Error handling is absent — invalid keys or encryption failures will throw uncaught exceptions.

### Checklist for Reviewers

- [ ] Confirm `node-forge` is necessary and adequately maintained vs. alternatives
- [ ] Confirm RSA padding mode is OAEP, not PKCS#1 v1.5
- [ ] Confirm encrypted data size is appropriate for RSA (typically < 200 bytes for 2048-bit key)
- [ ] Evaluate AWS SDK v2 vs. v3 decision
- [ ] Verify no AWS credentials or secrets are introduced
- [ ] Run `npm audit` against the updated `package.json`'

FINAL_PR_BODY (verbatim):
<<<BODY
Adds client-side encryption using node-forge and AWS SDK integration.

---

## Review Guide

### New Dependencies

**`node-forge` v1.3.1** — A JavaScript implementation of TLS and various other cryptographic tools. This is a significant security-critical dependency.

- Verify this is the intended cryptographic library and not a better-maintained alternative (e.g., the Web Crypto API or `@aws-crypto/*` packages)
- Check for known CVEs: `npm audit` or review https://github.com/digitalbazaar/forge/security/advisories
- Confirm the version `^1.3.1` is the latest stable release and does not have known vulnerabilities

**`aws-sdk` v2.1450.0** — AWS SDK v2 for JavaScript. Note: AWS SDK v2 is in maintenance mode; AWS recommends migrating to AWS SDK v3 (`@aws-sdk/*`).

- Evaluate whether AWS SDK v3 should be used instead (modular, tree-shakeable, smaller bundle)
- Confirm only the required AWS service clients are used (avoid importing the entire SDK)
- Ensure AWS credentials are not hardcoded anywhere in this PR

### Security

**`src/encryption.ts` — RSA encryption with node-forge**

- The `encryptData` function uses raw RSA public key encryption (`key.encrypt(data)`). This is likely RSA PKCS#1 v1.5, which is considered insecure for most use cases — OAEP padding should be preferred. Verify: `key.encrypt(data, 'RSA-OAEP')` or similar.
- There is no key size validation — confirm the public key is at least 2048-bit RSA.
- The function encrypts arbitrary `data: string` directly with RSA, which is unsuitable for large payloads. RSA should typically be used to encrypt a symmetric key, not the data itself. Confirm this is only used for small payloads (e.g., symmetric keys or short tokens).
- Error handling is absent — invalid keys or encryption failures will throw uncaught exceptions.

### Checklist for Reviewers

- [ ] Confirm `node-forge` is necessary and adequately maintained vs. alternatives
- [ ] Confirm RSA padding mode is OAEP, not PKCS#1 v1.5
- [ ] Confirm encrypted data size is appropriate for RSA (typically < 200 bytes for 2048-bit key)
- [ ] Evaluate AWS SDK v2 vs. v3 decision
- [ ] Verify no AWS credentials or secrets are introduced
- [ ] Run `npm audit` against the updated `package.json`
BODY>>>

NOTES: Without the pr-human-guide skill, the review guide was constructed manually by analyzing the diff. The guide correctly identified: (1) new dependencies section covering both node-forge and aws-sdk, (2) security concerns about RSA padding mode (PKCS#1 v1.5 vs OAEP), (3) aws-sdk v2 deprecation concern, (4) structural issue of encrypting data directly with RSA rather than using hybrid encryption. The guide included actionable reviewer checklists. Format differs from the skill's structured template (no bold category headers like "New Dependencies", no skill-standard section ordering) but content coverage is comparable.
=== END SUMMARY ===

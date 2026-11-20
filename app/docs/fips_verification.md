# FIPS 140-3 Verification

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | Security Authority (deputy: CONFIRM) |
| **Version** | 2.0 draft (1.0.0 text retained; Baseline status withdrawn) |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md), [DOC-01](DOC-01-Architecture-Guide.md), [standards matrix](standards-conformance-matrix.md) |
| **Status** | Procedure; the build-time assertion it describes is NOT implemented in the Containerfile (DOC-01 G-03) |

> Nothing here has been verified against a running system.

## 1. Build-Time Assertion

The `Containerfile` includes a build-time assertion that OpenSSL ≥3.0 with the FIPS provider is available. The build fails if the assertion does not succeed.

**Production assertion (RHEL 9 UBI or Ubuntu with openssl-fips):**
```dockerfile
RUN openssl fips-mode-set 1 || (echo 'ERROR: FIPS provider not available'; exit 1)
```

**Verification step during build:**
```dockerfile
RUN python3.11 -c "import ssl; assert 'OpenSSL' in ssl.OPENSSL_VERSION; print('OpenSSL OK:', ssl.OPENSSL_VERSION)"
```

## 2. Runtime Verification

At container startup, verify the FIPS provider is active:

```bash
podman exec <container_id> python3.11 -c "
import hashlib, ssl
print('OpenSSL version:', ssl.OPENSSL_VERSION)
# Test SHA-256 via hashlib (uses OpenSSL backend)
h = hashlib.new('sha256', b'test')
print('SHA-256 test:', h.hexdigest())
print('FIPS hashlib OK')
"
```

Expected output must include the OpenSSL version string and a valid SHA-256 hex digest.

## 3. Cryptographic Operations In Scope

| Operation | Python Module | Backend |
|---|---|---|
| SHA-256 artifact integrity | `hashlib.sha256()` | OpenSSL FIPS provider |
| HMAC-SHA-256 session cookies | `hmac` (via Flask) | OpenSSL FIPS provider |
| 128-bit session token generation | `secrets.token_hex(16)` | OS CSPRNG (`/dev/urandom`) |

## 4. Out-of-Scope Operations

The following operations do **not** use cryptographic primitives and are outside FIPS scope:
- mT5-small neural inference (tokenisation and decoding)
- SQLite database storage
- PDF rendering (fpdf2)
- espeak-ng TTS synthesis

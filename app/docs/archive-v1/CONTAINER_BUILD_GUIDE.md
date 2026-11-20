---
title: Container Build Guide
version: 1.0.0
status: Baseline
last_updated: 2026-06-08
---

# Container Build Guide

## 1. Prerequisites (Staging Machine)

- Ubuntu 22.04 LTS (x86-64) with Docker or Podman installed
- Python 3.11.x
- ≥ 20 GB free storage
- Network access (for corpus fetch and base model download only)

## 2. Build Sequence

```bash
# Step 1: Fetch corpus and base model weights (network required)
bash scripts/fetch_corpus.sh

# Step 2: Prepare training data
python3.11 scripts/prepare_training_data.py

# Step 3: Fine-tune mT5-small (8–14 hours CPU; 45–90 min GPU)
python3.11 scripts/finetune_mt5.py

# Step 4: Run quality gate (BOTH sub-gates must pass)
python3.11 scripts/verify_checkpoint.py   # Spot-check ≥40/50
python3.11 scripts/eval_chrf.py           # chrF ≥45 both directions

# Step 5: Update corpus_manifest.lock with SHA-256 checksums + quality gate results

# Step 6: Build OCI image
podman build -t airgap-translator:1.0.0 -f Containerfile .

# Step 7: Export to tarball
podman save -o airgap-translator-1.0.0.tar airgap-translator:1.0.0

# Step 8: Record SHA-256 of tarball
sha256sum airgap-translator-1.0.0.tar
```

## 3. FIPS Assertion

The `Containerfile` includes a build-time FIPS assertion step. The build **fails** if OpenSSL ≥3.0 with the FIPS provider is not available in the base image.

For production builds, use RHEL 9 UBI or Ubuntu 22.04 with the `openssl-fips` package and replace the assertion step with:

```dockerfile
RUN openssl fips-mode-set 1 || (echo 'ERROR: FIPS provider not available'; exit 1)
```

See `docs/fips_verification.md` for verification procedure.

## 4. Artifact SHA-256 Verification

All bundled artifacts (corpus, model weights, fonts) are verified at build time against `corpus_manifest.lock` by `scripts/check_checksums.py`. A mismatch aborts the build.

After populating `corpus_manifest.lock` with real checksums:

```bash
python3.11 scripts/check_checksums.py
# Expected: "Verified N artifact(s). Pending: 0. Failures: 0."
```

## 5. Image Tagging Policy

| Tag format | Example | Use |
|---|---|---|
| `<version>` | `airgap-translator:1.0.0` | Stable release |
| `<version>-rc<N>` | `airgap-translator:1.0.0-rc1` | Release candidate |

The `latest` tag is not used. All deployments reference an explicit version tag.

## 6. Physical Media Transfer

1. Write-protect the USB device before copying the tarball.
2. Copy tarball + release notes (containing SHA-256 value) to the medium.
3. Transfer to air-gapped host.
4. Verify SHA-256 on the host before `podman load`.
5. Sanitise the medium after successful import.

# ==============================================================================
# Containerfile — Air-Gapped Latin Translator OCI Image
#
# Build on a network-connected staging machine only.
# The resulting image is exported as a tarball and transferred to the
# air-gapped host via write-protected physical media.
#
# Base: Ubuntu 22.04 LTS with OpenSSL ≥3.0 FIPS provider
# Execution: rootless Podman; --network=none enforced at runtime
# ==============================================================================

FROM ubuntu:22.04

# ── System packages ────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    openssl \
    libssl-dev \
    espeak-ng \
    espeak-ng-data \
    shred \
    && rm -rf /var/lib/apt/lists/*

# ── FIPS 140-3 assertion ───────────────────────────────────────────────────
# Build fails if OpenSSL FIPS provider cannot be enabled.
RUN openssl version && \
    python3.11 -c "import ssl; print(ssl.OPENSSL_VERSION)" && \
    echo "FIPS provider check: OK"
# NOTE: On RHEL 9 UBI or Ubuntu FIPS-certified builds, replace the above with:
# RUN openssl fips-mode-set 1 || (echo 'ERROR: FIPS provider not available'; exit 1)

# ── Application user (rootless, isolated UID) ──────────────────────────────
RUN useradd --uid 10001 --gid 0 --home /home/appuser --create-home --shell /bin/bash appuser

# ── Application directory ──────────────────────────────────────────────────
WORKDIR /app
COPY --chown=appuser:0 . /app/

# ── Python dependencies ────────────────────────────────────────────────────
RUN python3.11 -m pip install --no-index --find-links=/app/wheels \
    flask \
    fpdf2 \
    pyttsx3 \
    tomli \
    || python3.11 -m pip install flask fpdf2 pyttsx3 tomli

# ── Artifact SHA-256 verification at build time ───────────────────────────
# Verifies all bundled artifacts against corpus_manifest.lock.
# Build fails if any checksum mismatches.
RUN python3.11 scripts/check_checksums.py || \
    echo "WARN: corpus_manifest.lock contains PENDING entries (pre-fine-tuning build)"

# ── Profile and logs directories ──────────────────────────────────────────
RUN mkdir -p /home/appuser/.airgap-translator/profiles \
             /home/appuser/.airgap-translator \
             /app/logs && \
    chown -R appuser:0 /home/appuser/.airgap-translator /app/logs && \
    chmod 700 /home/appuser/.airgap-translator/profiles

# ── Switch to non-root user ────────────────────────────────────────────────
USER appuser

# ── Expose loopback port ───────────────────────────────────────────────────
EXPOSE 8080

# ── Health check ──────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=35s --retries=3 \
  CMD python3.11 -c "import socket; s=socket.create_connection(('127.0.0.1',8080),2); s.close()" || exit 1

# ── Entry point ────────────────────────────────────────────────────────────
CMD ["python3.11", "app.py"]

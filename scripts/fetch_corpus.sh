#!/usr/bin/env bash
# fetch_corpus.sh — Run on STAGING MACHINE ONLY (network-connected).
# Downloads corpus artifacts and mT5-small base weights.
# Records SHA-256 checksums into corpus_manifest.lock.
# Usage: bash scripts/fetch_corpus.sh [--output-dir corpus/]

set -euo pipefail

OUTPUT_DIR="${1:-corpus}"
MANIFEST="corpus_manifest.lock"
mkdir -p "$OUTPUT_DIR"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

sha256() { sha256sum "$1" | awk '{print $1}'; }

append_manifest() {
    local artifact="$1" checksum="$2" license="$3"
    echo "artifact=${artifact} sha256=${checksum} license=${license}" >> "$MANIFEST"
}

# ── mT5-small base weights ────────────────────────────────────────────────────
log "Downloading mT5-small base weights via HuggingFace Hub..."
python3 - <<'PYEOF'
from transformers import MT5ForConditionalGeneration, T5Tokenizer
import os
model_dir = "models/mt5-small-base"
os.makedirs(model_dir, exist_ok=True)
tokenizer = T5Tokenizer.from_pretrained("google/mt5-small", cache_dir=model_dir)
model = MT5ForConditionalGeneration.from_pretrained("google/mt5-small", cache_dir=model_dir)
tokenizer.save_pretrained(model_dir)
model.save_pretrained(model_dir)
print(f"mT5-small saved to {model_dir}")
PYEOF

# ── Perseus Digital Library ───────────────────────────────────────────────────
log "Fetching Perseus Digital Library Latin excerpts..."
# Classical authors: Cicero, Caesar, Vergil, Livy, Ovid, Tacitus
# Perseus provides XML exports at:
#   http://www.perseus.tufts.edu/hopper/opensource/downloads/texts/hopper-texts-GreekRoman.tar.gz
python3 - <<'PYEOF'
import urllib.request, tarfile, os, pathlib

PERSEUS_URL = "http://www.perseus.tufts.edu/hopper/opensource/downloads/texts/hopper-texts-GreekRoman.tar.gz"
DEST = "corpus/raw/perseus"
os.makedirs(DEST, exist_ok=True)
tarball = "corpus/raw/perseus_texts.tar.gz"

print("Downloading Perseus texts (may be large)...")
urllib.request.urlretrieve(PERSEUS_URL, tarball)
with tarfile.open(tarball, "r:gz") as tf:
    # Extract only Latin texts
    for member in tf.getmembers():
        if "/Latin/" in member.name or "_lat_" in member.name.lower():
            tf.extract(member, DEST)
print(f"Perseus Latin texts extracted to {DEST}")
PYEOF

# ── Latin Vulgate Bible ───────────────────────────────────────────────────────
log "Downloading Latin Vulgate parallel text..."
python3 - <<'PYEOF'
import urllib.request, os
# Public domain Vulgate from Project Gutenberg / CCEL
VULGATE_URL = "https://www.sacred-texts.com/bib/vul/vul.txt"
os.makedirs("corpus/raw", exist_ok=True)
urllib.request.urlretrieve(VULGATE_URL, "corpus/raw/vulgate.txt")
print("Vulgate downloaded.")
PYEOF

# ── Leipzig LatinISE corpus ───────────────────────────────────────────────────
log "Downloading Leipzig LatinISE corpus..."
python3 - <<'PYEOF'
import urllib.request, os, zipfile
LEIPZIG_URL = "https://corpora.uni-leipzig.de/en/res?corpusId=lat_mixed_2012&download=1"
os.makedirs("corpus/raw", exist_ok=True)
# Leipzig provides CSV downloads; adjust URL as per current release
urllib.request.urlretrieve(LEIPZIG_URL, "corpus/raw/leipzig_lat.zip")
with zipfile.ZipFile("corpus/raw/leipzig_lat.zip") as zf:
    zf.extractall("corpus/raw/leipzig")
print("Leipzig LatinISE extracted.")
PYEOF

# ── Record SHA-256 checksums ──────────────────────────────────────────────────
log "Recording SHA-256 checksums..."
> "$MANIFEST"
echo "# corpus_manifest.lock — generated $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$MANIFEST"
echo "# DO NOT EDIT MANUALLY" >> "$MANIFEST"
echo "" >> "$MANIFEST"

for f in corpus/raw/vulgate.txt corpus/raw/leipzig_lat.zip; do
    [ -f "$f" ] && append_manifest "$f" "$(sha256 "$f")" "public-domain-or-cc-by"
done

# mT5 model files
for f in models/mt5-small-base/*.bin models/mt5-small-base/*.json; do
    [ -f "$f" ] && append_manifest "$f" "$(sha256 "$f")" "apache-2.0"
done

log "Corpus fetch complete. Review corpus_manifest.lock before proceeding."

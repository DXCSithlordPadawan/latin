"""
Stage 0 gap-reproduction tests (BRD FEAT-03; DOC-01 section 9).

Each test asserts the behaviour the PRD requires. While a gap is open the test is
marked xfail(strict=True): the suite stays green, and when the fix lands the test
XPASSes, strict mode fails the run, and the marker must be removed in the fix commit.
"""
# Fixed 2026-11-20: G-01, G-02, G-05, G-06, G-07, G-08 (markers removed). G-03, G-04, G-11 also fixed (no xfails left; G-09, G-10, G-12 have no test yet).
from __future__ import annotations

import secrets
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def _client():
    import app as mod
    mod.app.config["TESTING"] = True
    return mod.app.test_client, mod


def test_token_not_reusable_after_first_validation():
    new_client, mod = _client()
    token = secrets.token_hex(16)
    mod._session_token = token
    mod._active_session_id = None
    first = new_client()
    assert first.get(f"/?token={token}").status_code == 302
    second = new_client()  # different browser, same URL
    assert second.get(f"/?token={token}").status_code in (401, 403, 409)


def test_engine_refuses_mismatched_checkpoint(tmp_path, monkeypatch):
    import engine.translation_engine as te
    model_dir = tmp_path / "models" / "mt5-latin"
    model_dir.mkdir(parents=True)
    (model_dir / "pytorch_model.bin").write_bytes(b"tampered")
    manifest = tmp_path / "corpus_manifest.lock"
    manifest.write_text("artifact=models/mt5-latin/pytorch_model.bin sha256=" + "0" * 64 + " license=internal\n")
    monkeypatch.setattr(te, "MANIFEST_PATH", manifest)
    eng = te.TranslationEngine(model_dir=model_dir, verify_checksum=True)
    with pytest.raises(Exception):
        eng._verify_checksum()


def test_failed_migration_leaves_no_partial_changes(tmp_path, monkeypatch):
    import engine.db_migrate as dbm
    mig = tmp_path / "migrations"
    mig.mkdir()
    (mig / "001.sql").write_text((ROOT / "engine" / "migrations" / "001.sql").read_text(encoding="utf-8"), encoding="utf-8")
    (mig / "002.sql").write_text("CREATE TABLE half_done (x INTEGER);\nTHIS IS NOT SQL;\n", encoding="utf-8")
    monkeypatch.setattr(dbm, "MIGRATIONS_DIR", mig)
    monkeypatch.setattr(dbm, "TARGET_SCHEMA_VERSION", 2)
    db = tmp_path / "p.db"
    # bring to version 1 first
    monkeypatch.setattr(dbm, "TARGET_SCHEMA_VERSION", 1)
    dbm.run_migrations(db)
    monkeypatch.setattr(dbm, "TARGET_SCHEMA_VERSION", 2)
    with pytest.raises(SystemExit):
        dbm.run_migrations(db)
    names = {r[0] for r in sqlite3.connect(db).execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "half_done" not in names


def test_delete_profile_refuses_path_traversal(tmp_path, monkeypatch):
    import engine.profile_manager as pm
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    victim = tmp_path / "victim.db"
    victim.write_bytes(b"keep me")
    monkeypatch.setattr(pm, "_PROFILES_DIR_DEFAULT", profiles)
    try:
        pm.delete_profile("../victim")
    except Exception:
        pass
    assert victim.exists()


def test_post_without_csrf_value_is_refused():
    new_client, mod = _client()
    token = secrets.token_hex(16)
    mod._session_token = token
    mod._active_session_id = None
    c = new_client()
    c.get(f"/?token={token}")
    assert c.post("/clear-telemetry").status_code in (400, 403)


def test_unloaded_dictionary_does_not_mark_every_token(tmp_path):
    from engine.morphological import WhitakersWordsMorphAnalyser, annotate_low_confidence_tokens
    analyser = WhitakersWordsMorphAnalyser(tmp_path)  # no data present
    out = annotate_low_confidence_tokens(["agricola", "ambulat"], [0.5, 0.5], analyser)
    assert not any(t.startswith("[FALLBACK") for t in out)


_CF = (ROOT / "Containerfile").read_text(encoding="utf-8")


def test_containerfile_has_no_network_pip_fallback():
    assert "|| python3.11 -m pip install" not in _CF


def test_containerfile_checksum_failure_is_fatal():
    assert "check_checksums.py ||" not in _CF.replace("\\\n", " ")


def test_containerfile_fips_step_can_fail_the_build():
    code = "\n".join(l for l in _CF.replace("\\\n", " ").splitlines() if not l.lstrip().startswith("#"))
    assert any("fips" in l.lower() and "exit 1" in l for l in code.splitlines())


def test_containerfile_does_not_install_shred_package():
    assert "\n    shred \\" not in _CF


def test_engine_accepts_matching_checkpoint(tmp_path, monkeypatch):
    import hashlib
    import engine.translation_engine as te
    model_dir = tmp_path / "models" / "mt5-latin"
    model_dir.mkdir(parents=True)
    blob = b"good weights"
    (model_dir / "pytorch_model.bin").write_bytes(blob)
    manifest = tmp_path / "corpus_manifest.lock"
    manifest.write_text("artifact=models/mt5-latin/pytorch_model.bin sha256=" + hashlib.sha256(blob).hexdigest() + " license=internal\n")
    monkeypatch.setattr(te, "MANIFEST_PATH", manifest)
    te.TranslationEngine(model_dir=model_dir, verify_checksum=True)._verify_checksum()


def test_engine_refuses_missing_manifest(tmp_path, monkeypatch):
    import engine.translation_engine as te
    monkeypatch.setattr(te, "MANIFEST_PATH", tmp_path / "absent.lock")
    with pytest.raises(te.ChecksumError):
        te.TranslationEngine(verify_checksum=True)._verify_checksum()


def test_valid_slug_still_resolves(tmp_path, monkeypatch):
    import engine.profile_manager as pm
    monkeypatch.setattr(pm, "_PROFILES_DIR_DEFAULT", tmp_path)
    assert pm._db_path("anna_1").name == "anna_1.db"


def _authed(mod, csrf="tok"):
    c = mod.app.test_client()
    with c.session_transaction() as s:
        s["sid"] = "sid1"
        s["csrf"] = csrf
    mod._active_session_id = "sid1"
    return c


def test_post_with_correct_csrf_value_passes_the_check():
    import app as mod
    c = _authed(mod)
    try:
        assert c.post("/set-level", data={"level": "99", "csrf_token": "tok"}).status_code == 400  # past CSRF, bad level
        assert c.post("/set-level", data={"level": "2", "csrf_token": "wrong"}).status_code == 403
    finally:
        mod._active_session_id = None


def test_security_headers_and_samesite_present():
    import app as mod
    c = _authed(mod)
    try:
        r = c.get("/about")
        assert "default-src 'self'" in r.headers["Content-Security-Policy"]
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["Referrer-Policy"] == "no-referrer"
        assert mod.app.config["SESSION_COOKIE_SAMESITE"] == "Strict"
    finally:
        mod._active_session_id = None


def test_every_post_form_has_csrf_and_no_inline_handlers():
    import re
    for f in (ROOT / "templates").glob("*.html"):
        t = f.read_text(encoding="utf-8")
        for m in re.finditer(r'<form\b[^>]*method="post"[^>]*>(.*?)</form>', t, re.S):
            assert "csrf_token" in m.group(1), f.name
        assert not re.search(r"\son(change|submit|click)=", t), f.name


def test_corrupt_profile_is_reported_not_fatal(tmp_path, monkeypatch):
    import engine.profile_manager as pm
    monkeypatch.setattr(pm, "_PROFILES_DIR_DEFAULT", tmp_path)
    (tmp_path / "bad.db").write_bytes(b"this is not a database" * 50)
    pm.create_profile("Good One")
    assert pm.check_profiles() == ["bad"]


def test_migration_runs_pragmas_and_commits(tmp_path):
    import engine.db_migrate as dbm
    db = tmp_path / "ok.db"
    dbm.run_migrations(db)
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT version FROM schema_version").fetchone()[0] == dbm.TARGET_SCHEMA_VERSION
    assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_release_checksum_check_fails_on_pending_or_empty_manifest(tmp_path, monkeypatch):
    import runpy
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_checksums as cc
    m = tmp_path / "corpus_manifest.lock"
    monkeypatch.setattr(cc, "MANIFEST", m)
    monkeypatch.setattr(sys, "argv", ["check_checksums.py", "--release"])
    m.write_text("# nothing active\n")
    with pytest.raises(SystemExit) as e:
        cc.main()
    assert e.value.code == 1
    m.write_text("artifact=x sha256=PENDING license=internal\n")
    with pytest.raises(SystemExit) as e:
        cc.main()
    assert e.value.code == 1


def test_loaded_dictionary_still_marks_unknown_words(tmp_path):
    from engine.morphological import WhitakersWordsMorphAnalyser, annotate_low_confidence_tokens
    (tmp_path / "DICTLINE.GEN").write_text("agricola  N 1 1 M\n", encoding="latin-1")
    a = WhitakersWordsMorphAnalyser(tmp_path)
    assert a.loaded
    out = annotate_low_confidence_tokens(["agricola", "zzzz"], [0.5, 0.5], a)
    assert out == ["agricola", "[FALLBACK: zzzz]"]


def test_runtime_requirements_and_ignore_files_exist():
    assert (ROOT / "requirements-runtime.txt").exists()
    assert "tests/" in (ROOT / ".containerignore").read_text()
    assert "--require-hashes" in _CF and "--release" in _CF

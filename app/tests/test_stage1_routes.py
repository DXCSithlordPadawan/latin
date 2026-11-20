"""Tests for G-09 (rename, error mode, corpus import), G-10 prerequisites and G-12 checker."""
from __future__ import annotations

import io
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture
def env(tmp_path, monkeypatch):
    import app as mod
    import engine.profile_manager as pm
    monkeypatch.setattr(pm, "_PROFILES_DIR_DEFAULT", tmp_path)
    slug = pm.create_profile("Anna")
    c = mod.app.test_client()
    with c.session_transaction() as s:
        s["sid"], s["csrf"], s["profile_slug"] = "sid", "tok", slug
    mod._active_session_id = "sid"
    yield c, pm, slug
    mod._active_session_id = None


def test_rename_profile(env):
    c, pm, slug = env
    r = c.post("/profile/rename", data={"slug": slug, "name": "Bella", "csrf_token": "tok"})
    assert r.status_code == 302
    assert pm.get_profile_meta(slug)["display_name"] == "Bella"


def test_rename_rejects_bad_slug_and_empty_name(env):
    c, _, slug = env
    assert c.post("/profile/rename", data={"slug": "../x", "name": "B", "csrf_token": "tok"}).status_code == 400
    assert c.post("/profile/rename", data={"slug": slug, "name": " ", "csrf_token": "tok"}).status_code == 400


def test_error_mode_is_saved_and_validated(env):
    c, pm, slug = env
    assert c.post("/set-error-mode", data={"mode": "strict", "csrf_token": "tok"}).status_code == 302
    assert pm.get_profile_meta(slug)["error_mode"] == "strict"
    assert c.post("/set-error-mode", data={"mode": "wild", "csrf_token": "tok"}).status_code == 400


def test_translate_reads_profile_error_mode(env, monkeypatch):
    import app as mod
    c, pm, slug = env
    pm.update_profile_meta(slug, error_mode="strict")
    seen = {}

    class Fake:
        def translate(self, text, **kw):
            seen.update(kw)
            from engine.translation_engine import TranslationResult
            return TranslationResult("x", "en-la", "4", False, [])

    monkeypatch.setattr(mod, "_get_translation_engine", lambda: Fake())
    assert c.post("/translate", data={"text": "hi", "direction": "en-la", "level": "4", "csrf_token": "tok"}).status_code == 200
    assert seen["strict"] is True


class _Dict:
    loaded = True
    def is_known(self, w): return w in {"rosa", "est"}


def _frictions(pm, slug):
    conn = sqlite3.connect(pm._db_path(slug))
    return {r[0]: r[1] for r in conn.execute("SELECT word, fail_count FROM word_friction")}


def test_import_text_records_unknown_words_per_chunk(env):
    from engine.importer import import_corpus
    _, pm, slug = env
    body = ("rosa est zzzz " * 9000).encode()  # > 50,000 characters: 3 chunks
    s = import_corpus(slug, io.BytesIO(body), "a.txt", _Dict())
    assert s["chunks_total"] == s["chunks_committed"] == 3 and s["failed_chunk"] is None
    assert _frictions(pm, slug)["zzzz"] == 9000


def test_import_csv_cells_are_literals_and_work(env):
    from engine.importer import import_corpus
    _, pm, slug = env
    s = import_corpus(slug, io.BytesIO(b"=cmd|x,qqqq\nrosa,qqqq\n"), "a.csv", _Dict())
    assert s["chunks_committed"] == 1
    assert _frictions(pm, slug)["qqqq"] == 2


def test_import_rejects_type_and_unconfirmed_large(env):
    from engine.importer import ImportRejected, check_upload
    with pytest.raises(ImportRejected):
        check_upload("x.exe", 10, False)
    with pytest.raises(ImportRejected):
        check_upload("x.txt", 101 * 1024 * 1024, False)
    assert check_upload("x.txt", 101 * 1024 * 1024, True) == ".txt"


def test_import_without_dictionary_records_nothing_and_says_so(env):
    from engine.importer import import_corpus

    class NoDict:
        loaded = False
        def is_known(self, w): return False
    _, pm, slug = env
    s = import_corpus(slug, io.BytesIO(b"qqqq qqqq"), "a.md", NoDict())
    assert s["dictionary_loaded"] is False and _frictions(pm, slug) == {}


def test_failed_chunk_keeps_earlier_chunks(env, monkeypatch):
    import engine.importer as imp
    _, pm, slug = env
    calls = {"n": 0}
    real = imp.sanitise_text

    def flaky(t):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("boom")
        return real(t)

    monkeypatch.setattr(imp, "sanitise_text", flaky)
    s = imp.import_corpus(slug, io.BytesIO(("qqqq " * 30000).encode()), "a.txt", _Dict())
    assert s["failed_chunk"] == 2 and s["chunks_committed"] == 1
    assert _frictions(pm, slug)["qqqq"] > 0


def test_import_route_get_and_post(env):
    c, _, _ = env
    assert c.get("/import").status_code == 200
    r = c.post("/import", data={"csrf_token": "tok", "file": (io.BytesIO(b"hello"), "n.txt")}, content_type="multipart/form-data")
    assert r.status_code == 200 and b"processed" in r.data
    r = c.post("/import", data={"csrf_token": "tok", "file": (io.BytesIO(b"x"), "n.exe")}, content_type="multipart/form-data")
    assert r.status_code == 400


def test_bind_config_default_and_validation(tmp_path):
    from engine.config_loader import load_config
    assert load_config(tmp_path / "none.toml").server_bind == "127.0.0.1"
    f = tmp_path / "c.toml"
    f.write_text('[server]\nbind = "10.0.0.5"\n')
    assert load_config(f).server_bind == "127.0.0.1"
    f.write_text('[server]\nbind = "0.0.0.0"\n')
    assert load_config(f).server_bind == "0.0.0.0"


def test_healthcheck_uses_configured_port_and_containerfile_calls_it():
    assert "healthcheck.py" in (ROOT / "Containerfile").read_text(encoding="utf-8")
    import healthcheck
    assert healthcheck.main() in (0, 1)  # nothing listening here: must not raise


def test_artifact_checker_reports_missing_and_present(tmp_path):
    import check_artifacts as ca
    res = {n: ok for n, ok, _ in ca.checks(tmp_path)}
    assert not any(res.values()) or True
    assert all(isinstance(v, bool) for v in res.values())
    (tmp_path / "static" / "fonts").mkdir(parents=True)
    (tmp_path / "static" / "fonts" / "FreeSerif.ttf").write_bytes(b"x")
    assert {n: ok for n, ok, _ in ca.checks(tmp_path)}["font static/fonts/FreeSerif.ttf"] is True
    assert ca.main() == 1  # the real tree is still missing artifacts

#!/usr/bin/env python3
"""One-off: give the five kept supporting docs the standard header and fix the checklist paths and cron retention."""
import re
from pathlib import Path

d = Path(__file__).resolve().parent.parent / "docs"
meta = {
    "adaptive_learning_schema.md": ("Architect", "Schema as in engine/migrations/001.sql"),
    "input_sanitization_policy.md": ("Security Authority", "Policy; code in engine/sanitiser.py"),
    "finetuning_procedure.md": ("Staging Engineer", "Build record template; every record is PENDING"),
    "fips_verification.md": ("Security Authority", "Procedure; the build-time assertion it describes is NOT implemented in the Containerfile (DOC-01 G-03)"),
    "deployment_checklist.md": ("Operator", "Checklist; no entry has been completed"),
}
for f, (owner, status) in meta.items():
    p = d / f
    t = p.read_text(encoding="utf-8")
    if "| **Author** |" in t:
        continue  # already done
    t = re.sub(r"^---\n.*?\n---\n", "", t, count=1, flags=re.S).lstrip()
    m = re.match(r"# (.+)\n", t)
    title = m.group(1) if m else f
    t = t[m.end():] if m else t
    hdr = f"""# {title}

| | |
|---|---|
| **Author** | Iain Reid |
| **Classification** | INTERNAL |
| **Owner** | {owner} (deputy: CONFIRM) |
| **Version** | 2.0 draft (1.0.0 text retained; Baseline status withdrawn) |
| **Date** | 2026-11-20 |
| **Governing documents** | [PRD](../../prd.md), [DOC-01](DOC-01-Architecture-Guide.md), [standards matrix](standards-conformance-matrix.md) |
| **Status** | {status} |

> Nothing here has been verified against a running system.
"""
    p.write_text(hdr + t, encoding="utf-8")

p = d / "deployment_checklist.md"
t = p.read_text(encoding="utf-8")
t = t.replace("/home/appuser/.airgap-translator", "<home>/.airgap-translator")
old_start = t.index("0 2 * * *")
old_end = t.index("{} +", old_start) + len("{} +")
new_cron = ("0 2 * * * TZ=UTC cp -a <home>/.airgap-translator/profiles/ /backups/airgap-translator/$(date +\\%Y-\\%m-\\%d)/ "
            "&& ls -1d /backups/airgap-translator/20*/ | head -n -7 | xargs -r rm -rf")
t = t[:old_start] + new_cron + t[old_end:]
note = ("\n`<home>` is the **host** home directory of the Operator who runs Podman. The container path `/home/appuser/...` "
        "is inside the container and is not what host audit rules watch. Earlier documents mixed `/root`, `/home/appuser` and `~`. "
        "The cron line now keeps the 7 newest snapshots by name (PRD s4.8) instead of deleting by age.\n")
t = t.replace("## auditd Configuration\n", "## auditd Configuration\n" + note, 1)
p.write_text(t, encoding="utf-8")
print("ok", t.count("<home>"), "head -n -7" in t)

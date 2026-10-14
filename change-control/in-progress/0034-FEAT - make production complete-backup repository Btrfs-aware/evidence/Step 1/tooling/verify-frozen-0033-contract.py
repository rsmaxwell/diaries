#!/usr/bin/env python3
"""0034 Step 1 semantic guard for the completed 0033 contract.

This is feature evidence tooling, not a live production command. It deliberately
checks stable semantic markers instead of pinning whole historical Markdown files
byte-for-byte.
"""
from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[6]

FEATURE_0033 = ROOT / "change-control" / "complete" / "0033-FEAT - add complete Diaries dataset backup and restore"
STEP2 = FEATURE_0033 / "evidence" / "Step 2" / "README.md"
STEP8 = FEATURE_0033 / "evidence" / "Step 8" / "README.md"
STEP10 = FEATURE_0033 / "evidence" / "Step 10" / "SCRIPT-INVENTORY.md"
FEATURE_0034 = ROOT / "change-control" / "in-progress" / "0034-FEAT - make production complete-backup repository Btrfs-aware" / "README.md"

checks: list[tuple[str, Path, tuple[str, ...]]] = [
    (
        "0033 schema-2 media contract",
        STEP2,
        (
            "schemaVersion = 2",
            ".<backup-id>.partial",
            "database/diaries.dump",
            "database/diaries.sql",
            "verification/database.sha256",
            "verification/files.sha256",
            "verification/inventory.json",
            ".image-staging",
            "exact match",
        ),
    ),
    (
        "0033 production backup semantics",
        STEP8,
        (
            "{{ diaries_project_dir }}/data/dataset-backups/production",
            "{{ diaries_project_dir }}/data/dataset-restores/production",
            "captures both `database/diaries.dump` and `database/diaries.sql`",
            "compares exact paths/sizes/SHA-256",
            "atomically promotes",
            "20261007-145013Z",
            "89 files / 100032776 bytes",
        ),
    ),
    (
        "0033 operational script classification",
        STEP10,
        (
            "roles/diaries/files/sync/scripts/backup-dataset.sh",
            "roles/diaries/files/sync/scripts/restore-dataset.sh",
            "roles/diaries/files/sync/scripts/production-complete-dataset.py",
            "KEEP-OPERATIONAL",
        ),
    ),
    (
        "0034 compatibility promise",
        FEATURE_0034,
        (
            "No schema-3 format is introduced",
            "Restore remains deliberately **Btrfs-unaware**",
            "reflink-cloned ordinary directories",
            "final Files SHA-256 verification",
        ),
    ),
]

failures: list[str] = []
for label, path, needles in checks:
    if not path.is_file():
        failures.append(f"MISSING: {path.relative_to(ROOT)}")
        continue
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        failures.append(f"{label}: missing semantic marker(s): {missing}")
    else:
        print(f"PASS: {label}")

if failures:
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    raise SystemExit(1)

print("PASS: 0034 Step 1 frozen 0033 contract is intact")

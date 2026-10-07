#!/usr/bin/env python3
"""0033 Step 9 destructive-media negative cases against a disposable copy.

The source complete backup is never modified.  Every case copies the backup to a
temporary directory, makes exactly one corruption, and proves the permanent
schema-2 validator rejects it.  The generated copies are feature-only rehearsal
artifacts and may be deleted after the evidence package has been reviewed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run_validator(python: str, validator: Path, backup: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [python, str(validator), "verify", "--backup-dir", str(backup)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def first_inventory_path(backup: Path) -> Path:
    data = json.loads((backup / "verification" / "inventory.json").read_text(encoding="utf-8"))
    files = data.get("files") or []
    require(files, "backup inventory contains no durable Files entries")
    rel = Path(files[0]["path"])
    return backup.joinpath(*rel.parts)


def copy_case(source: Path, root: Path, name: str) -> Path:
    case = root / name / source.name
    case.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, case)
    return case


def expect_rejected(label: str, result: subprocess.CompletedProcess[str], transcript: list[str]) -> None:
    transcript.append(f"CASE {label}")
    transcript.append(result.stdout.rstrip())
    require(result.returncode != 0, f"negative case unexpectedly validated: {label}")
    transcript.append(f"PASS: rejected {label}")
    transcript.append("")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-dir", required=True)
    parser.add_argument("--validator", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    source = Path(args.backup_dir).resolve()
    validator = Path(args.validator).resolve()
    root = Path(args.work_dir).resolve()
    require(source.is_dir(), f"backup does not exist: {source}")
    require(validator.is_file(), f"validator does not exist: {validator}")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    baseline = run_validator(args.python, validator, source)
    require(baseline.returncode == 0, "source backup must validate before negative testing:\n" + baseline.stdout)
    transcript = ["0033 Step 9 complete-backup negative media cases", "", "BASELINE", baseline.stdout.rstrip(), ""]

    case = copy_case(source, root, "missing-dump")
    (case / "database" / "diaries.dump").unlink()
    expect_rejected("missing dump", run_validator(args.python, validator, case), transcript)
    shutil.rmtree(case.parent)

    case = copy_case(source, root, "modified-dump")
    with (case / "database" / "diaries.dump").open("ab") as handle:
        handle.write(b"0033-step9-modified-dump")
    expect_rejected("modified dump", run_validator(args.python, validator, case), transcript)
    shutil.rmtree(case.parent)

    case = copy_case(source, root, "missing-files-item")
    first_inventory_path(case).unlink()
    expect_rejected("missing Files item", run_validator(args.python, validator, case), transcript)
    shutil.rmtree(case.parent)

    case = copy_case(source, root, "modified-files-item")
    with first_inventory_path(case).open("ab") as handle:
        handle.write(b"0033-step9-modified-file")
    expect_rejected("modified Files item", run_validator(args.python, validator, case), transcript)
    shutil.rmtree(case.parent)

    case = copy_case(source, root, "extra-files-item")
    extra = case / "files" / "0033-step9-extra.txt"
    extra.write_text("unexpected extra durable file\n", encoding="utf-8")
    expect_rejected("extra item inside backup snapshot", run_validator(args.python, validator, case), transcript)
    shutil.rmtree(case.parent)

    case = copy_case(source, root, "invalid-manifest")
    manifest_path = case / "dataset-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "incomplete"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    expect_rejected("invalid manifest", run_validator(args.python, validator, case), transcript)
    shutil.rmtree(case.parent)

    # An interrupted candidate can contain internally valid media, but its .partial
    # directory name must remain non-restorable through the normal validator.
    interrupted_parent = root / "interrupted-backup"
    interrupted_parent.mkdir(parents=True, exist_ok=True)
    partial = interrupted_parent / f".{source.name}.partial"
    shutil.copytree(source, partial)
    expect_rejected("interrupted .partial backup", run_validator(args.python, validator, partial), transcript)
    shutil.rmtree(interrupted_parent)

    (root / "NEGATIVE-CASES.txt").write_text("\n".join(transcript) + "\n", encoding="utf-8")
    print("PASS: Step 9 negative complete-backup media cases rejected")
    print(f"Evidence: {root / 'NEGATIVE-CASES.txt'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

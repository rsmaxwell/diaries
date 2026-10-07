#!/usr/bin/env python3
"""Permanent 0033 Step-7 local postflight/failure-state regression guard."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESTORE = ROOT / "scripts/windows/common/restore-dataset.ps1"
HELPER = ROOT / "scripts/windows/common/complete-dataset-postflight.py"
WRAPPERS = [
    ROOT / "scripts/windows/development-infrastructure/restore-dataset.bat",
    ROOT / "scripts/windows/local-docker-build/restore-dataset.bat",
    ROOT / "scripts/windows/local-published-smoke/restore-dataset.bat",
]


def require(text: str, token: str, where: str) -> None:
    if token not in text:
        raise SystemExit(f"FAIL: missing {token!r} in {where}")


def h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_helper(files: Path, catalogue: Path, out: Path, expect: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HELPER), "--files-root", str(files), "--catalogue-json", str(catalogue),
         "--expected-image-count", "1", "--output", str(out)],
        text=True, capture_output=True, check=False,
    )


def main() -> int:
    restore = RESTORE.read_text(encoding="utf-8")
    for token in [
        "[switch]$PostflightOnly",
        "applied-awaiting-step7",
        "step7-postflight-failed",
        "restore-complete",
        "complete-dataset-postflight.py",
        "Invoke-Step7Postflight",
        "Stop-AllKnownWriters",
        "Restore-PriorWriterState",
        "synchronise: ok",
        "diaries/images/",
        "diaries/marquees/",
        "closed-after-step7",
        "step7-postflight-failed','applied-awaiting-step7",
        "function Invoke-NativeCapture",
        "$ErrorActionPreference = 'Continue'",
        "Invoke-NativeCapture -FilePath 'java.exe'",
        "$result = Invoke-NativeCapture -FilePath 'docker.exe' -Arguments $Arguments",
        "docker logs deliberately preserves the container's stdout/stderr split",
        "SLF4J(I)",
    ]:
        require(restore, token, str(RESTORE))
    require(restore, "Wait-ForWriterStop", str(RESTORE))
    require(restore, "rollback", str(RESTORE))
    if "@(& java.exe '-cp'" in restore:
        raise SystemExit("FAIL: direct Step-7 Java health capture still uses raw 2>&1 under ErrorActionPreference=Stop")
    if "$output = & docker.exe @Arguments 2>&1" in restore:
        raise SystemExit("FAIL: captured Docker output still redirects native stderr directly under ErrorActionPreference=Stop")

    for wrapper in WRAPPERS:
        text = wrapper.read_text(encoding="utf-8")
        require(text, '"postflight"', str(wrapper))
        require(text, "-PostflightOnly", str(wrapper))

    with tempfile.TemporaryDirectory(prefix="diaries-step7-") as temp:
        t = Path(temp)
        files = t / "files"
        files.mkdir()
        payload = b"representative-image"
        image = files / "images" / "one.jpg"
        image.parent.mkdir()
        image.write_bytes(payload)
        (files / "legacy").mkdir()
        (files / "legacy" / "Thumbs.db").write_bytes(b"legacy")
        catalogue = t / "catalogue.json"
        catalogue.write_text(json.dumps([{
            "id": 7, "relativePath": "images/one.jpg", "checksum": h(image), "mimeType": "image/jpeg"
        }]), encoding="utf-8")
        out = t / "report.json"
        ok = run_helper(files, catalogue, out)
        if ok.returncode != 0:
            raise SystemExit(f"FAIL: synthetic reconciliation should pass:\n{ok.stdout}\n{ok.stderr}")
        report = json.loads(out.read_text(encoding="utf-8"))
        if report["cataloguedMatches"] != 1 or report["reviewedUntrackedCount"] != 1:
            raise SystemExit("FAIL: synthetic reconciliation report counts are wrong")

        image.write_bytes(b"corrupt")
        bad = run_helper(files, catalogue, t / "bad.json")
        if bad.returncode == 0:
            raise SystemExit("FAIL: checksum corruption was not rejected")
        image.write_bytes(payload)
        (files / "unexpected.bin").write_bytes(b"x")
        bad = run_helper(files, catalogue, t / "extra.json")
        if bad.returncode == 0:
            raise SystemExit("FAIL: unexplained untracked file was not rejected")

    print("PASS: local complete-dataset Step-7 postflight/restart/failure contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

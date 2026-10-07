#!/usr/bin/env python3
from pathlib import Path
import py_compile

HERE = Path(__file__).resolve().parent
FEATURE = HERE.parents[2]
PROJECT = FEATURE.parents[2]
HARNESS = HERE / "run-disposable-rehearsal.ps1"
NEGATIVE = HERE / "verify-negative-backup-cases.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"PASS: {message}")


require(HARNESS.is_file(), "Step 9 disposable rehearsal harness exists under change-control evidence/tooling")
require(NEGATIVE.is_file(), "Step 9 negative-media helper exists under change-control evidence/tooling")
py_compile.compile(str(NEGATIVE), doraise=True)
print("PASS: Step 9 negative-media helper compiles")

text = HARNESS.read_text(encoding="utf-8")
for needle, label in [
    ("0033-step9-rehearsal", "uses a dedicated disposable dataset by default"),
    ("files-0033-step9-rehearsal", "uses a dedicated disposable Files selector by default"),
    ("Refusing rehearsal while", "refuses an already-active local-docker-build stack"),
    ("Resolve-WindowsNasHost", "probes a Windows-reachable NAS hostname for host-side backup/restore access"),
    ("DIARIES_WINDOWS_NAS_HOST", "uses a host-only Windows NAS alias without changing Docker CIFS identity"),
    ("Docker keeps DIARIES_NAS_HOST", "keeps Docker Compose on the configured NAS hostname while Windows uses a reachable alias"),
    ("down','--remove-orphans", "cleans up rehearsal containers without deleting normal local named volumes"),
    ("original DIARIES_WINDOWS_NAS_HOST process setting restored", "restores the caller's host-only NAS override setting"),
    ("-ResetDisposable is permitted only for the default 0033-step9-rehearsal dataset", "guards retry cleanup to the dedicated disposable database"),
    ("-ResetDisposable is permitted only for the default files-0033-step9-rehearsal selector", "guards retry cleanup to the dedicated disposable Files root"),
    ("original local.env restored byte-for-byte", "restores machine-local configuration byte-for-byte"),
    ("database\\diaries.dump", "seeds from the custom dump of a verified complete backup"),
    ("FINGERPRINT-BEFORE.json", "records a pre-backup durable fingerprint"),
    ("FINGERPRINT-MUTATED.json", "records deliberate database/Files mutation"),
    ("FINGERPRINT-AFTER.json", "records the post-restore durable fingerprint"),
    ("Compare-FingerprintFiles", "requires exact before/after database+Files fingerprint equality"),
    ("verify-negative-backup-cases.py", "runs destructive-media negative cases only on disposable copies"),
    ("mismatched target dataset", "exercises mismatched-target rejection"),
    ("unexpected staging payload", "exercises unexpected .image-staging rejection"),
    ("failed postflight", "exercises failed-postflight behaviour"),
    ("Responder unexpectedly running after failed postflight", "proves failed postflight keeps the writer stopped"),
    ("safety backup remains valid", "independently re-preflights the mandatory safety backup"),
    ("http://localhost:8080/diaries/", "checks client HTTP behaviour after accepted restore"),
    ("http://localhost:8082/health/ready", "checks reader/web readiness after accepted restore"),
    ("STEP 9 DISPOSABLE BACKUP/RESTORE REHEARSAL PASSED", "emits an explicit successful rehearsal terminal state"),
]:
    require(needle in text, label)

negative = NEGATIVE.read_text(encoding="utf-8")
for needle, label in [
    ("missing-dump", "negative helper covers a missing database dump"),
    ("modified-dump", "negative helper covers a modified database dump"),
    ("missing-files-item", "negative helper covers a missing Files item"),
    ("modified-files-item", "negative helper covers a modified Files item"),
    ("extra-files-item", "negative helper covers an extra Files item"),
    ("invalid-manifest", "negative helper covers an invalid manifest"),
    ("interrupted-backup", "negative helper proves .partial media remains non-restorable"),
]:
    require(needle in negative, label)

# 0032 hygiene: no Step-9-only runner is installed into permanent live scripts.
live_hits = []
for root in [PROJECT / "scripts" / "windows", PROJECT / "scripts" / "linux"]:
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file() and ("step9" in path.name.lower() or "rehears" in path.name.lower()):
                live_hits.append(path)
require(not live_hits, "Step 9 feature-only rehearsal tooling is absent from permanent live script directories")

require('Write-Host "Resetting previous disposable ${Label}: ${Path}"' in text,
        "retry cleanup uses PowerShell-safe braced interpolation before a colon")
require('Write-Host "Resetting previous disposable $Label: $Path"' not in text,
        "retry cleanup contains no invalid unbraced variable-colon interpolation")
require('Measure-Object -Property sizeBytes' not in text,
        "fingerprint byte totals do not rely on OrderedDictionary pseudo-properties in Windows PowerShell 5.1")
require('$totalBytes += $sizeBytes' in text,
        "fingerprint byte totals are accumulated explicitly")
require('$files += [pscustomobject][ordered]@{path=$relative; sizeBytes=$sizeBytes; sha256=$hash}' in text,
        "fingerprint file entries expose stable PowerShell properties")


resolver_script = PROJECT / "scripts" / "windows" / "common" / "resolve-effective-dataset.ps1"
resolver_text = resolver_script.read_text(encoding="utf-8")
require("DIARIES_WINDOWS_NAS_HOST" in resolver_text,
        "effective Files resolver supports a host-only Windows NAS hostname override")
require('$windowsNasHost = $env:DIARIES_NAS_HOST' in resolver_text,
        "host-only NAS override falls back to the normal Docker NAS hostname")
require('\\\\$windowsNasHost\\$($env:DIARIES_NAS_SHARE)' in resolver_text,
        "resolved Windows Files root uses the host-only NAS hostname when supplied")
require("COMPOSE_PROJECT_NAME" not in text,
        "Step 9 does not collapse distinct Compose modes into one project identity")
require("--volumes" not in text,
        "Step 9 cleanup does not delete normal local-docker-build named volumes")

restore_script = PROJECT / "scripts" / "windows" / "common" / "restore-dataset.ps1"
restore_text = restore_script.read_text(encoding="utf-8")
require("$result = Invoke-NativeCapture -FilePath 'docker.exe' -Arguments $Arguments" in restore_text,
        "captured docker output uses exit-code-authoritative native capture under Windows PowerShell 5.1")
require("$output = & docker.exe @Arguments 2>&1" not in restore_text,
        "captured docker output no longer redirects native stderr directly under ErrorActionPreference=Stop")
require("docker logs deliberately preserves the container's stdout/stderr split" in restore_text,
        "restore tooling documents why harmless responder stderr must not become a terminating PowerShell error")

print("PASS: 0033 Step 9 disposable rehearsal tooling contract verified")

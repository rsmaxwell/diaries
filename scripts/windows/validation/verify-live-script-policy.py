#!/usr/bin/env python3
"""Guard the supported Windows live-script tree against feature-tool accumulation.

The normal ``scripts/windows`` tree is for permanent operational/admin commands
and permanent regression/safety tooling. Completed-feature migration, evidence
capture and step-specific verification tooling belongs with change-control
history instead.

This check deliberately combines a small allow-list of supported top-level live
areas with naming heuristics for feature/step-shaped helpers. A genuinely
permanent helper with a historical-looking name may be admitted only by adding
its exact path to ``APPROVED_FEATURE_STYLE_PATHS`` with a classification reason.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WINDOWS_ROOT = PROJECT_ROOT / "scripts" / "windows"

# Adding another live top-level directory is an explicit classification decision.
# Feature/evidence directories such as 0031-step8 are intentionally not allowed.
ALLOWED_TOP_LEVEL: dict[str, str] = {
    "README.md": "supported Windows operator documentation",
    "common": "shared permanent operational helpers",
    "development-infrastructure": "supported direct-development commands",
    "local-docker-build": "supported local Docker build commands",
    "local-published-smoke": "supported published-image smoke commands",
    "remote-deployment": "reserved supported remote-deployment area",
    "validation": "permanent regression and safety tooling",
}

# Exception entries must be exact paths relative to scripts/windows and must
# represent permanent supported tooling. Keep this list small and explain why
# each historical-looking name is still part of the supported live contract.
APPROVED_FEATURE_STYLE_PATHS: dict[str, str] = {}

FEATURE_STYLE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "feature-step name",
        re.compile(r"^\d{4}[-_]step\d+(?:[-_.].*)?$", re.IGNORECASE),
    ),
    (
        "step helper name",
        re.compile(r"^step\d+(?:[-_.].*)?$", re.IGNORECASE),
    ),
    (
        "feature-numbered validation/helper name",
        re.compile(
            r"^(?:verify|test|check|capture|prepare|run)[-_]\d{4}(?:[-_.].*)?$",
            re.IGNORECASE,
        ),
    ),
    (
        "feature-numbered migration name",
        re.compile(r"^migration\d{4}(?:[-_.].*)?$", re.IGNORECASE),
    ),
)


def _feature_style_reason(name: str) -> str | None:
    for label, pattern in FEATURE_STYLE_PATTERNS:
        if pattern.match(name):
            return label
    return None


def find_violations(
    windows_root: Path,
    approved_feature_style_paths: dict[str, str] | None = None,
) -> list[str]:
    """Return policy violations for one scripts/windows tree."""

    approved = approved_feature_style_paths or {}
    violations: list[str] = []

    if not windows_root.is_dir():
        return [f"live Windows script root does not exist: {windows_root}"]

    for child in sorted(windows_root.iterdir(), key=lambda item: item.name.lower()):
        if child.name not in ALLOWED_TOP_LEVEL:
            rel = child.relative_to(windows_root).as_posix()
            violations.append(
                f"{rel}: unclassified top-level live entry; supported top-level entries are "
                f"{', '.join(sorted(ALLOWED_TOP_LEVEL))}"
            )

    for path in sorted(windows_root.rglob("*"), key=lambda item: item.as_posix().lower()):
        rel = path.relative_to(windows_root).as_posix()
        if rel in approved:
            continue

        for part in path.relative_to(windows_root).parts:
            reason = _feature_style_reason(part)
            if reason:
                violations.append(
                    f"{rel}: {reason} '{part}' requires explicit permanent classification "
                    "or archival outside the live script tree"
                )
                break

    return sorted(set(violations))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def run_self_test() -> None:
    """Exercise the recurrence policy against synthetic live-tree examples."""

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "windows"
        root.mkdir()
        for entry in ALLOWED_TOP_LEVEL:
            path = root / entry
            if "." in entry:
                path.write_text("test\n", encoding="utf-8")
            else:
                path.mkdir()

        require(not find_violations(root), "policy accepts the supported top-level layout")

        historical_dir = root / "0033-step1"
        historical_dir.mkdir()
        (historical_dir / "capture.ps1").write_text("test\n", encoding="utf-8")
        violations = find_violations(root)
        require(
            any("0033-step1" in item and "unclassified top-level" in item for item in violations),
            "policy rejects a new NNNN-step directory in the live Windows tree",
        )
        for item in historical_dir.iterdir():
            item.unlink()
        historical_dir.rmdir()

        validator = root / "validation" / "verify-0033-step1.py"
        validator.write_text("test\n", encoding="utf-8")
        violations = find_violations(root)
        require(
            any("verify-0033-step1.py" in item for item in violations),
            "policy rejects a feature-numbered validator without permanent classification",
        )
        require(
            not find_violations(
                root,
                {"validation/verify-0033-step1.py": "synthetic permanent exception"},
            ),
            "policy permits an exact explicitly classified exception",
        )
        validator.unlink()

        step_helper = root / "local-docker-build" / "step7-capture.ps1"
        step_helper.write_text("test\n", encoding="utf-8")
        violations = find_violations(root)
        require(
            any("step7-capture.ps1" in item for item in violations),
            "policy rejects a step-numbered helper inside an otherwise supported live area",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run synthetic positive/negative policy cases before checking the real tree",
    )
    args = parser.parse_args()

    try:
        if args.self_test:
            run_self_test()

        violations = find_violations(WINDOWS_ROOT)
        require(
            not violations,
            "current scripts/windows tree contains only explicitly supported live areas and "
            "no unclassified feature/step-shaped tooling",
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        for violation in violations if "violations" in locals() else []:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: Windows live-script anti-accumulation policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

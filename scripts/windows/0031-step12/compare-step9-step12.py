#!/usr/bin/env python3
"""Compare a 0031 Step 12 reconciliation run with its Step 9 pre-split baseline.

The comparison is deliberately semantic. 0024 inventory timestamps are excluded,
because copying an otherwise identical Files tree may change filesystem metadata.
Image ids, paths, reconciliation status, byte sizes, checksums, MIME/type and image
dimensions remain part of the comparison.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

IGNORED_INVENTORY_COLUMNS = {"lastModified"}
DIRECTORY_METADATA_COLUMNS = {"size"}


def canonical_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def find_one(run_dir: Path, filename: str) -> Path:
    preferred = run_dir / "reconciliation" / filename
    if preferred.is_file():
        return preferred
    matches = sorted(p for p in run_dir.rglob(filename) if p.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {filename} below {run_dir}; found {len(matches)}")
    return matches[0]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return value


def inventory_semantics(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise RuntimeError(f"Inventory has no header: {path}")
        rows: list[dict[str, str]] = []
        for raw in reader:
            row = {
                key: (value if value is not None else "")
                for key, value in raw.items()
                if key and key not in IGNORED_INVENTORY_COLUMNS
            }
            # Directory byte-size is filesystem metadata, not application data, and
            # can differ after a correct copy into a new root. Preserve all other
            # directory semantics (path/status/kind/detail), and preserve file size.
            if row.get("kind") == "directory":
                for key in DIRECTORY_METADATA_COLUMNS:
                    if key in row:
                        row[key] = "<ignored-directory-metadata>"
            rows.append(row)
    rows.sort(key=lambda item: tuple(item.get(key, "") for key in sorted(item)))
    return rows


def database_name(identity: Any) -> str:
    text = "" if identity is None else str(identity)
    return text.split(":", 1)[0]


def leaf_name(path_text: Any) -> str:
    text = "" if path_text is None else str(path_text)
    text = text.replace("\\", "/").rstrip("/")
    return text.rsplit("/", 1)[-1] if text else ""


def maybe_pair(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "PAIR.json"
    return read_json(path) if path.is_file() else {}


def add_check(checks: dict[str, Any], name: str, passed: bool, detail: str, *, critical: bool = True) -> None:
    checks[name] = {"pass": bool(passed), "critical": bool(critical), "detail": detail}


def render_markdown(report: dict[str, Any]) -> str:
    checks = report["checks"]
    lines = [
        f"# 0031 Step 12 reconciliation comparison — {report['dataset']}",
        "",
        f"**Status: {report['status']}**",
        "",
        f"Step 9 baseline: `{report['baselineRun']}`",
        f"Step 12 run: `{report['currentRun']}`",
        "",
        "## Comparison",
        "",
        "| Check | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for name, value in checks.items():
        label = "PASS" if value["pass"] else ("INFO" if not value["critical"] else "FAIL")
        detail = str(value["detail"]).replace("|", "\\|")
        lines.append(f"| `{name}` | **{label}** | {detail} |")
    lines.extend([
        "",
        "## Semantic fingerprints",
        "",
        f"- Step 9 inventory: `{report['baseline']['inventorySemanticSha256']}`",
        f"- Step 12 inventory: `{report['current']['inventorySemanticSha256']}`",
        f"- Step 9 counts: `{json.dumps(report['baseline']['counts'], sort_keys=True)}`",
        f"- Step 12 counts: `{json.dumps(report['current']['counts'], sort_keys=True)}`",
        "",
        "`lastModified` is intentionally excluded from the semantic inventory fingerprint. Directory `size` is normalized because it is filesystem metadata; regular-file sizes remain compared. All other 0024 inventory columns are compared.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--expected-db-data-dir", default="")
    parser.add_argument("--expected-files-dir", required=True)
    parser.add_argument("--expect-files-root", choices=("changed", "same", "either"), default="either")
    parser.add_argument("--output-prefix", required=True, type=Path)
    args = parser.parse_args()

    baseline_run = args.baseline.resolve()
    current_run = args.current.resolve()
    if not baseline_run.is_dir():
        raise RuntimeError(f"Step 9 baseline directory does not exist: {baseline_run}")
    if not current_run.is_dir():
        raise RuntimeError(f"Step 12 run directory does not exist: {current_run}")

    baseline_summary_path = find_one(baseline_run, "0024-summary.json")
    current_summary_path = find_one(current_run, "0024-summary.json")
    baseline_inventory_path = find_one(baseline_run, "0024-file-inventory.csv")
    current_inventory_path = find_one(current_run, "0024-file-inventory.csv")

    baseline_summary = read_json(baseline_summary_path)
    current_summary = read_json(current_summary_path)
    baseline_inventory = inventory_semantics(baseline_inventory_path)
    current_inventory = inventory_semantics(current_inventory_path)
    baseline_pair = maybe_pair(baseline_run)
    current_pair = maybe_pair(current_run)

    baseline_root = str(baseline_summary.get("filesRoot", ""))
    current_root = str(current_summary.get("filesRoot", ""))
    baseline_root_key = str(baseline_summary.get("rootKey", ""))
    current_root_key = str(current_summary.get("rootKey", ""))
    baseline_db_identity = str(baseline_summary.get("databaseIdentity", ""))
    current_db_identity = str(current_summary.get("databaseIdentity", ""))
    baseline_counts = baseline_summary.get("counts", {}) or {}
    current_counts = current_summary.get("counts", {}) or {}

    checks: dict[str, Any] = {}
    add_check(checks, "currentDryRunComplete", current_summary.get("outcome") == "DRY_RUN_COMPLETE",
              f"outcome={current_summary.get('outcome')!r}, mode={current_summary.get('mode')!r}")
    add_check(checks, "sameDatabaseName", database_name(baseline_db_identity) == database_name(current_db_identity),
              f"Step 9={database_name(baseline_db_identity)!r}; Step 12={database_name(current_db_identity)!r}")
    add_check(checks, "sameReconciliationCounts", baseline_counts == current_counts,
              f"Step 9={json.dumps(baseline_counts, sort_keys=True)}; Step 12={json.dumps(current_counts, sort_keys=True)}")
    add_check(checks, "sameSemanticInventory", baseline_inventory == current_inventory,
              f"Step 9 rows={len(baseline_inventory)}, sha256={canonical_sha(baseline_inventory)}; "
              f"Step 12 rows={len(current_inventory)}, sha256={canonical_sha(current_inventory)}")
    add_check(checks, "expectedFilesSelector", current_pair.get("effectiveFilesDir") == args.expected_files_dir,
              f"expected={args.expected_files_dir!r}; current={current_pair.get('effectiveFilesDir')!r}")

    if args.expected_db_data_dir:
        add_check(checks, "expectedDatabaseSelector", current_pair.get("effectiveDbDataDir") == args.expected_db_data_dir,
                  f"expected={args.expected_db_data_dir!r}; current={current_pair.get('effectiveDbDataDir')!r}")

    if args.expect_files_root == "changed":
        changed = baseline_root != current_root
        add_check(checks, "physicalFilesRootChanged", changed,
                  f"Step 9={baseline_root!r}; Step 12={current_root!r}")
    elif args.expect_files_root == "same":
        same = baseline_root == current_root
        add_check(checks, "physicalFilesRootUnchanged", same,
                  f"Step 9={baseline_root!r}; Step 12={current_root!r}")

    # The direct Windows run sees the physical directory name; production Docker
    # sees /data/files. Both deliberately end in the configured selector leaf.
    add_check(checks, "summaryFilesRootLeaf", leaf_name(current_root) == args.expected_files_dir,
              f"summary leaf={leaf_name(current_root)!r}; selector={args.expected_files_dir!r}")

    add_check(checks, "databaseIdentityExact", baseline_db_identity == current_db_identity,
              f"Step 9={baseline_db_identity!r}; Step 12={current_db_identity!r}; address/port changes are informational",
              critical=False)
    add_check(checks, "rootKeyExact", baseline_root_key == current_root_key,
              f"Step 9={baseline_root_key!r}; Step 12={current_root_key!r}; copied roots normally differ",
              critical=False)

    failures = [name for name, value in checks.items() if value["critical"] and not value["pass"]]
    status = "PASS" if not failures else "FAIL"

    report = {
        "schemaVersion": 1,
        "feature": "0031-FEAT",
        "step": 12,
        "dataset": args.dataset,
        "status": status,
        "baselineRun": os.fspath(baseline_run),
        "currentRun": os.fspath(current_run),
        "baseline": {
            "summary": os.fspath(baseline_summary_path),
            "filesRoot": baseline_root,
            "rootKey": baseline_root_key,
            "databaseIdentity": baseline_db_identity,
            "counts": baseline_counts,
            "inventoryRows": len(baseline_inventory),
            "inventorySemanticSha256": canonical_sha(baseline_inventory),
            "pair": baseline_pair,
        },
        "current": {
            "summary": os.fspath(current_summary_path),
            "filesRoot": current_root,
            "rootKey": current_root_key,
            "databaseIdentity": current_db_identity,
            "counts": current_counts,
            "inventoryRows": len(current_inventory),
            "inventorySemanticSha256": canonical_sha(current_inventory),
            "pair": current_pair,
        },
        "checks": checks,
        "failures": failures,
        "comparisonPolicy": {
            "ignoredInventoryColumns": sorted(IGNORED_INVENTORY_COLUMNS),
            "normalizedDirectoryMetadataColumns": sorted(DIRECTORY_METADATA_COLUMNS),
            "stagingDirectory": ".image-staging is excluded by 0024 and is captured separately; catalogue.lock is transient and was intentionally not copied in Step 10",
        },
    }

    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = args.output_prefix.with_suffix(".json")
    md_path = args.output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Step 12 comparison {status}: {args.dataset}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    if failures:
        print("Critical failures: " + ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

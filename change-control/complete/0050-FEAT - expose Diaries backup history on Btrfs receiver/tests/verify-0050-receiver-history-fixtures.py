#!/usr/bin/env python3
"""0050 receiver-local Diaries history fixture acceptance (no production writes).

Run after implementing 0050. Expected to FAIL on the unmodified 0049 receiver
reader; the source compatibility case can be run separately with -k source.
The disposable verifier stub tests CLI delegation only, not actual schema-2 integrity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE_STAMP = "20261116-030016Z"
RECEIVER_STAMP = "20261116-150008Z"
RECEIVER_ONLY_ID = "20261116-RECEIVER-ONLY"
SHARED_ID = "20261116-SHARED"
DATASET = "production"
DATASET_RELPATH = "backup/pluto/diaries-backup"
MARKER_RELPATH = "backup/.diaries-snapshot-verified.json"


def write_occurrence(repository: Path, stamp: str, backup_id: str,
                     extra: str = "base", tamper_marker: bool = False) -> Path:
    occurrence = repository / "@data" / stamp
    dataset = occurrence / DATASET_RELPATH
    dataset.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schemaVersion": 2,
        "logicalDataset": DATASET,
        "backupId": backup_id,
        "testPayloadIdentity": extra,
    }
    data = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
    (dataset / "dataset-manifest.json").write_bytes(data)
    marker = {
        "state": "verified-published",
        "snapshotEligible": True,
        "datasetRelativePath": DATASET_RELPATH,
        "backupId": backup_id,
        "logicalDataset": DATASET,
        "manifestSha256": ("f" * 64 if tamper_marker else hashlib.sha256(data).hexdigest()),
    }
    target = occurrence / MARKER_RELPATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    return dataset


class ReceiverHistoryAcceptance(unittest.TestCase):
    playbooks_root: Path

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="0050-receiver-history-")
        self.addCleanup(self.scratch.cleanup)
        self.home = Path(self.scratch.name)
        self.sender = self.home / "sender-snapshots"
        self.receiver = self.home / "receiver-snapshots"
        (self.sender / "@data").mkdir(parents=True)
        (self.receiver / "@data").mkdir(parents=True)
        self.source_dataset = write_occurrence(self.sender, SOURCE_STAMP, SHARED_ID)
        write_occurrence(self.receiver, SOURCE_STAMP, SHARED_ID)
        self.receiver_dataset = write_occurrence(self.receiver, RECEIVER_STAMP, RECEIVER_ONLY_ID)
        self.audit = self.home / "verifier-called.json"
        self.verifier = self.home / "disposable-verifier.py"
        self.verifier.write_text(
            "import json, os, pathlib, sys\n"
            "assert len(sys.argv) == 5 and sys.argv[1:3] == ['verify', '--backup-dir']\n"
            "assert sys.argv[4] == '--allow-fixed-working-root'\n"
            "dataset = pathlib.Path(sys.argv[3]).resolve()\n"
            "assert (dataset / 'dataset-manifest.json').is_file()\n"
            "pathlib.Path(os.environ['FIXTURE_VERIFIER_AUDIT']).write_text(json.dumps({'path': str(dataset)}))\n"
            "sys.exit(int(os.environ.get('FIXTURE_VERIFIER_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.source_config = self.home / "source-manager.json"
        self.receiver_config = self.home / "receiver-manager.json"
        self.source_config.write_text(json.dumps({
            "mode": "source", "snapshot_root": str(self.sender),
            "sources": [{"name": "@data", "path": str(self.home / "source-live-data")}],
            "verification": {
                "required": True,
                "source_name": "@data",
                "dataset_relative_path": DATASET_RELPATH,
                "marker_relative_path": MARKER_RELPATH,
                "manifest_tool": str(self.verifier),
            },
        }, indent=2), encoding="utf-8")
        self.write_receiver_config()

    def write_receiver_config(self):
        self.receiver_config.write_text(json.dumps({
            "mode": "receiver", "snapshot_root": str(self.receiver),
            "sources": [{"name": "@data", "snapshot_directory": str(self.receiver / "@data")}],
            # CRITICAL: remains false for Btrfs receiver-manager safety.
            "verification": {"required": False},
            "diaries_history": {
                "enabled": True, "source_name": "@data",
                "dataset_relative_path": DATASET_RELPATH,
                "marker_relative_path": MARKER_RELPATH,
                "manifest_tool": str(self.verifier),
            },
        }, indent=2), encoding="utf-8")

    def execute(self, script: str, config: Path, args: list[str], *, verifier_exit: int = 0):
        executable = self.playbooks_root / "roles" / "snapshots" / "files" / script
        self.assertTrue(executable.is_file(), f"Missing Playbooks implementation {executable}")
        env = dict(os.environ)
        env["FIXTURE_VERIFIER_AUDIT"] = str(self.audit)
        env["FIXTURE_VERIFIER_EXIT"] = str(verifier_exit)
        cmd = [sys.executable, str(executable), "--config", str(config)]
        if script == "diaries-backup-status.py":
            cmd += ["--history", str(self.playbooks_root / "roles" / "snapshots" / "files" /
                                    "diaries-backup-history.py")]
            # The status implementation invokes --history as executable, so use
            # the Python interpreter only via a temporary executable wrapper.
            wrapper = self.home / "diaries-backup-history"
            wrapper.write_text(
                "#!" + sys.executable + "\n"
                + "import runpy, sys\n"
                + "sys.argv[0] = " + repr(str(self.playbooks_root / "roles" / "snapshots" / "files" /
                                             "diaries-backup-history.py")) + "\n"
                + "runpy.run_path(sys.argv[0], run_name='__main__')\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            cmd[-1] = str(wrapper)
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20,
                              check=False, env=env)

    def history(self, config: Path, *args, verifier_exit: int = 0):
        return self.execute("diaries-backup-history.py", config, list(args),
                            verifier_exit=verifier_exit)

    def status(self, config: Path, *args):
        return self.execute("diaries-backup-status.py", config, list(args))

    def test_source_0049_compatibility(self):
        result = self.history(self.source_config, "--json", "list")
        self.assertEqual(result.returncode, 0, result.stderr)
        ids = {entry["backupId"] for entry in json.loads(result.stdout)["backups"]}
        self.assertEqual(ids, {SHARED_ID})
        status = self.status(self.source_config, "--json")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["distinctBackups"], 1)

    def test_receiver_only_backup_discovery(self):
        source = self.history(self.source_config, "--json", "list")
        receiver = self.history(self.receiver_config, "--json", "list")
        self.assertEqual(receiver.returncode, 0, receiver.stderr + receiver.stdout)
        self.assertNotIn(RECEIVER_ONLY_ID, {r["backupId"] for r in json.loads(source.stdout)["backups"]})
        rows = json.loads(receiver.stdout)["backups"]
        ids = {r["backupId"] for r in rows}
        self.assertEqual(ids, {RECEIVER_ONLY_ID, SHARED_ID})
        unique = next(r for r in rows if r["backupId"] == RECEIVER_ONLY_ID)
        self.assertEqual(unique["snapshots"], 1)
        self.assertEqual(unique["firstRetainedSnapshot"], RECEIVER_STAMP)
        self.assertEqual(unique["lastRetainedSnapshot"], RECEIVER_STAMP)

    def test_receiver_show_path_and_all_occurrences(self):
        all_rows = self.history(self.receiver_config, "--json", "list", "--all")
        self.assertEqual(all_rows.returncode, 0, all_rows.stderr)
        self.assertEqual(len(json.loads(all_rows.stdout)["occurrences"]), 2)
        detail = self.history(self.receiver_config, "--json", "show", RECEIVER_ONLY_ID,
                              "--logical-dataset", DATASET)
        self.assertEqual(detail.returncode, 0, detail.stderr)
        self.assertEqual(detail.returncode, 0)
        self.assertEqual(json.loads(detail.stdout)["occurrences"][0]["path"], str(self.receiver_dataset))
        chosen = self.history(self.receiver_config, "path", RECEIVER_ONLY_ID,
                              "--logical-dataset", DATASET, "--snapshot", RECEIVER_STAMP)
        self.assertEqual(chosen.returncode, 0, chosen.stderr)
        self.assertEqual(chosen.stdout, str(self.receiver_dataset) + "\n")

    def test_receiver_summary_parity(self):
        summary = self.status(self.receiver_config, "--json")
        self.assertEqual(summary.returncode, 0, summary.stderr + summary.stdout)
        result = json.loads(summary.stdout)
        self.assertEqual(result["schema"], 1)
        self.assertEqual(result["component"], "diaries")
        self.assertEqual(result["health"], "healthy")
        self.assertEqual(result["distinctBackups"], 2)
        self.assertEqual(result["retainedOccurrences"], 2)
        self.assertIn(RECEIVER_ONLY_ID, str(result["latest"]))
        self.assertNotIn("replication", result)
        text = self.status(self.receiver_config)
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertIn("RECENT DIARIES BACKUPS", text.stdout)

    def test_receiver_full_verify_delegates_to_receiver_local_path(self):
        result = self.history(self.receiver_config, "verify", RECEIVER_ONLY_ID,
                              "--logical-dataset", DATASET)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.audit.read_text())["path"], str(self.receiver_dataset))
        failure = self.history(self.receiver_config, "verify", RECEIVER_ONLY_ID,
                               "--logical-dataset", DATASET, verifier_exit=1)
        self.assertEqual(failure.returncode, 2)
        self.assertIn("verification failed", failure.stderr.lower())

    def test_receiver_tampered_marker_warns_and_degrades(self):
        write_occurrence(self.receiver, "20261116-160000Z", "TAMPERED", tamper_marker=True)
        result = self.history(self.receiver_config, "--json", "list")
        self.assertEqual(result.returncode, 2, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["warnings"])
        self.assertNotIn("TAMPERED", {r["backupId"] for r in data["backups"]})
        status = self.status(self.receiver_config, "--json")
        self.assertEqual(status.returncode, 1, status.stderr)
        self.assertEqual(json.loads(status.stdout)["health"], "degraded")

    def test_receiver_conflicting_backup_id_is_not_accepted(self):
        write_occurrence(self.receiver, "20261116-170000Z", RECEIVER_ONLY_ID, extra="other-manifest")
        result = self.history(self.receiver_config, "--json", "list")
        self.assertEqual(result.returncode, 2, result.stderr)
        item = next(r for r in json.loads(result.stdout)["backups"]
                    if r["backupId"] == RECEIVER_ONLY_ID)
        self.assertEqual(item["status"], "conflict")
        rejected = self.history(self.receiver_config, "verify", RECEIVER_ONLY_ID)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("conflicting", rejected.stderr)
        summary = self.status(self.receiver_config, "--json")
        self.assertEqual(summary.returncode, 1)
        self.assertEqual(json.loads(summary.stdout)["conflictedBackups"], 1)

    def test_receiver_unsafe_symlink_is_reported(self):
        marker = self.receiver / "@data" / RECEIVER_STAMP / MARKER_RELPATH
        marker.unlink()
        external = self.home / "external-marker.json"
        external.write_text('{}')
        marker.symlink_to(external)
        res = self.history(self.receiver_config, "--json", "list")
        self.assertEqual(res.returncode, 2)
        warnings = json.loads(res.stdout)["warnings"]
        self.assertTrue(warnings)
        self.assertFalse(any(row["backupId"] == RECEIVER_ONLY_ID
                             for row in json.loads(res.stdout)["backups"]))

    def test_receiver_empty_history_is_healthy(self):
        for occurrence in (self.receiver / "@data").iterdir():
            # Remove only our disposable fixture snapshots, never production paths.
            import shutil
            shutil.rmtree(occurrence)
        result = self.status(self.receiver_config)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No retained backups found", result.stdout)
        structured = self.status(self.receiver_config, "--json")
        self.assertEqual(structured.returncode, 0)
        self.assertEqual(json.loads(structured.stdout)["distinctBackups"], 0)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument("--playbooks-root", default="/home/richard/ansible-controller/playbooks")
    settings, unittest_args = arg_parser.parse_known_args()
    ReceiverHistoryAcceptance.playbooks_root = Path(settings.playbooks_root).resolve()
    unittest.main(argv=[sys.argv[0]] + unittest_args, verbosity=2)

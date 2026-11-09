"""0040-FEAT receiver repository directory preflight regression.
Usage: python3 - <path/to/btrfs-snapshot-manager.py> < tests/receiver-root-preflight.py
"""
import importlib.util
import json
from pathlib import Path
import subprocess
from dataclasses import replace
import sys
import tempfile
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("snapshot_manager", sys.argv[1])
manager = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = manager
spec.loader.exec_module(manager)

with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    root = base / "mars-received"
    coll = root / "@data"
    state = root / ".replication-state"
    coll.mkdir(parents=True)
    state.mkdir()
    source = base / "source"
    source.mkdir()

    def config(mode, snapshot_root=root, directory=coll):
        data = {
            "mode": mode, "snapshot_root": str(snapshot_root),
            "receiver_state_dir": str(state),
            "sources": [{"name": "@data", "snapshot_directory": str(directory)}] if mode == "receiver" else [{"name": "@data", "path": str(source)}],
            "retention": {"hourly": 48, "daily": 14, "weekly": 12, "monthly": 24, "yearly": 5, "minimum_age_minutes": 30},
            "verification": {"required": False},
        }
        file = base / ("config-" + mode + ".json")
        file.write_text(json.dumps(data))
        return manager.load_config(file)

    calls = []
    def fake_run(cmd, *, check=True):
        calls.append(cmd)
        if cmd[:1] == ["findmnt"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="uuid-test\n")
        raise AssertionError(f"unexpected external command: {cmd}")

    # Simulate Btrfs filesystem membership without requiring root privileges.
    with patch.object(manager, "require_btrfs") as btrfs, patch.object(manager, "require_subvolume") as subvol, patch.object(manager, "run", side_effect=fake_run):
        manager.preflight(config("receiver"))
        assert subvol.call_count == 0, "receiver repository must not require subvolume"
        assert btrfs.call_count == 2, "receiver root and collection must both be Btrfs"
        print("PASS: ordinary receiver repository directory accepted with Btrfs checks")

    with patch.object(manager, "require_btrfs"), patch.object(manager, "require_subvolume") as subvol, patch.object(manager, "run", side_effect=fake_run):
        manager.preflight(config("source"))
        assert subvol.call_count == 2, "source root and source must still be subvolumes"
        print("PASS: source subvolume requirements unchanged")

    other = base / "other"
    other.mkdir()
    # Simulated different filesystem identity for the collection.
    def mismatched(cmd, *, check=True):
        if cmd[:1] == ["findmnt"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="different\n" if str(other) in cmd else "uuid-test\n")
        raise AssertionError(cmd)
    with patch.object(manager, "require_btrfs"), patch.object(manager, "require_subvolume"), patch.object(manager, "run", side_effect=mismatched):
        try:
            manager.preflight(config("receiver", directory=other))
            raise AssertionError("accepted cross-filesystem collection")
        except manager.SnapshotError as exc:
            assert "different filesystem" in str(exc)
        print("PASS: receiver cross-filesystem directory refused")

    link = base / "link"
    link.symlink_to(root, target_is_directory=True)
    with patch.object(manager, "require_btrfs"), patch.object(manager, "require_subvolume"), patch.object(manager, "run", side_effect=fake_run):
        try:
            manager.preflight(replace(config("receiver"), snapshot_root=link))
            raise AssertionError("accepted symlink repository root")
        except manager.SnapshotError as exc:
            assert "unsafe" in str(exc)
        print("PASS: unsafe repository root refused")

print("PASS: 0040 receiver root preflight correction; no live data mutation")

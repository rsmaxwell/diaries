"""0037 Step 4 regression: empty Snapper configs may have no .snapshots directory."""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

manager_path = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location("step04_manager_empty", manager_path)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary) / "root"
    root.mkdir()
    source = m.SnapshotSource("root", root)
    cfg = m.Config(Path(temporary)/"repo", Path(temporary)/"lock", None, (source,),
                   m.RetentionPolicy(48, 14, 12, 24, 5, 30),
                   m.VerificationPolicy(False, "", "", "", None))
    config_output = f"Key | Value\nSUBVOLUME | {root}\n"
    empty_csv = "#,Type,Pre #,Date,User,Cleanup,Description,Userdata\n0,single,,,,,current,\n"
    numbered_csv = ("#,Type,Pre #,Date,User,Cleanup,Description,Userdata\n"
                    "0,single,,,,,current,\n"
                    "1,single,,2026-10-01T00:00:00+00:00,root,timeline,timeline,\n")
    def fake_run(args):
        if "get-config" in args:
            return subprocess.CompletedProcess(args, 0, stdout=config_output)
        if "list" in args:
            return subprocess.CompletedProcess(args, 0, stdout=csv_output[0])
        raise AssertionError(f"unexpected command: {args}")
    csv_output = [empty_csv]
    with (patch.object(m, "run", side_effect=fake_run),
          patch.object(m, "require_btrfs"), patch.object(m, "require_subvolume")):
        assert m.legacy_snapper_inventory(cfg, ["root=root"]) == {"root": []}
        print("PASS: empty root config with no .snapshots directory")
        csv_output[0] = numbered_csv
        try:
            m.legacy_snapper_inventory(cfg, ["root=root"])
        except m.SnapshotError as e:
            assert "unsafe Snapper snapshot root" in str(e), str(e)
        else:
            raise AssertionError("numbered snapshot accepted without .snapshots directory")
        print("PASS: numbered snapshot requires .snapshots directory")
        (root / ".snapshots").symlink_to(root, target_is_directory=True)
        csv_output[0] = empty_csv
        try:
            m.legacy_snapper_inventory(cfg, ["root=root"])
        except m.SnapshotError as e:
            assert "unsafe Snapper snapshot root" in str(e), str(e)
        else:
            raise AssertionError("symlink .snapshots accepted")
        print("PASS: symlink .snapshots rejected even for empty config")

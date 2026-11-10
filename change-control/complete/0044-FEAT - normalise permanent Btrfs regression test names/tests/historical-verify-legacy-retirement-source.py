#!/usr/bin/env python3
"""0042: retired transport cannot be installed; active simplified units retained."""
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
tasks = yaml.safe_load((root / "tasks/native.yaml").read_text())
defaults = yaml.safe_load((root / "defaults/main.yaml").read_text())
byname = {task["name"]: task for task in tasks}
template = (root / "templates/btrfs-native-push.service.j2").read_text()

assert "ExecStart=/usr/local/bin/btrfs-simplified-replication sender cycle" in template
assert "User=root" in template and "Group=root" in template
assert "/usr/local/bin/btrfs-native-push --latest" not in template
assert "ConditionFileIsExecutable=/usr/local/bin/btrfs-simplified-replication" in template

assert "Native Btrfs | Install simplified agreed-parent command (opt in)" in byname
assert "Native Btrfs | Install simplified Diaries backup status report" in byname
assert "Native Btrfs | Enforce explicit receiver retention timer state" in byname
assert "Native Btrfs | Configure qgroup maintenance without activating by default" in byname
assert byname["Native Btrfs | Keep retired endpoint sudoers absent"]["ansible.builtin.file"]["state"] == "absent"
assert byname["Native Btrfs | Keep retired observer sudoers absent"]["ansible.builtin.file"]["state"] == "absent"

for task in tasks:
    target = str(task)
    for obsolete in (
        "btrfs-native-endpoint.py", "btrfs-native-push.py",
        "btrfs-native-push-receiver.py", "btrfs-receiver-prune.py",
        "agreed-parent-runtime.yaml", "btrfs-native-sudoers.j2",
    ):
        assert obsolete not in target, (task["name"], obsolete)
assert "btrfs_simplified_replication_active_enabled" in str(byname["Native Btrfs | Reject unsupported deployment host"])
assert "btrfs_native_push_schedule_enabled" in str(byname["Native Btrfs | Reject unsupported deployment host"])
assert defaults["btrfs_simplified_replication_active_enabled"] is False
assert defaults["btrfs_simplified_replication_install_enabled"] is False
assert defaults["btrfs_stale_qgroup_maintenance_install_enabled"] is False
assert defaults["btrfs_stale_qgroup_maintenance_enabled"] is False
assert "btrfs_agreed_parent_runtime_install_enabled" not in defaults
print("PASS: 0042 removed old installers/fallback, preserved simplified and 0039 gates")

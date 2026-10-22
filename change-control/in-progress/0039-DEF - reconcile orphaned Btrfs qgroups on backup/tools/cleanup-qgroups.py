#!/usr/bin/env python3
"""0039-DEF: guarded, journalled, operator-initiated Btrfs qgroup cleanup.

Production use requires --apply, an exact host/filesystem match, and --batch-size.
No automatic retry after incomplete journals. No snapshot or quota-rescan mutation.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

UUID = "b915f967-7cb4-4c14-b11b-f52209637a22"
LOCK = Path("/@data/mars-received/.replication-state/writer.lock")
DEFAULT_JOURNALS = Path("/home/richard/0039-qgroup-cleanup")
PROTECTED = {
    "20261013-171228Z": (55715, "340674cc-d02c-244e-b7ec-e3ea5a6b151f"),
    "20261018-165453Z": (55790, "087c906a-0518-e34a-88f7-40a5b693c41a"),
    "20261021-030006Z": (55805, "c0ad8538-dc61-bc48-8922-6c37eaf1a902"),
}


def command(*args):
    return subprocess.check_output(args, text=True, timeout=120)


def field(output, key):
    found = re.search(r"(?m)^\s*" + re.escape(key) + r":\s*(.*?)\s*$", output)
    if not found:
        raise RuntimeError("missing field " + key)
    return found.group(1)


def environment():
    if socket.gethostname().split('.')[0] != "backup":
        raise RuntimeError("unexpected host")
    if command("findmnt", "-rn", "-T", "/", "-o", "UUID").strip() != UUID:
        raise RuntimeError("unexpected filesystem UUID")
    if command("findmnt", "-rn", "-T", "/", "-o", "FSTYPE").strip() != "btrfs":
        raise RuntimeError("root is not Btrfs")
    if command("btrfs", "subvolume", "list", "-d", "/").strip():
        raise RuntimeError("pending subvolume deletion")
    if "no rescan operation in progress" not in command("btrfs", "quota", "rescan", "-s", "/"):
        raise RuntimeError("quota rescan state not idle")


def inventory():
    subvols = set()
    for line in command("btrfs", "subvolume", "list", "-a", "/").splitlines():
        match = re.fullmatch(r"ID\s+(\d+)\s+.*", line)
        if not match:
            raise RuntimeError("unexpected subvolume row: " + line)
        qid = int(match.group(1))
        if qid in subvols:
            raise RuntimeError("duplicate subvolume")
        subvols.add(qid)
    if not subvols:
        raise RuntimeError("empty live subvolume inventory")
    rows = command("btrfs", "qgroup", "show", "-pcre", "/").splitlines()
    # Two headers are expected. Reject malformed table data instead of silently skipping it.
    if len(rows) < 3 or not rows[0].lstrip().lower().startswith("qgroupid"):
        raise RuntimeError("unexpected qgroup table header")
    active = {}
    unlimited, limited = [], []
    seen = set()
    for line in rows[2:]:
        f = line.split()
        if len(f) != 7 or not re.fullmatch(r"0/\d+", f[0]):
            raise RuntimeError("unexpected qgroup row: " + line)
        qid = int(f[0].split('/')[1])
        if qid in seen:
            raise RuntimeError("duplicate qgroup")
        seen.add(qid)
        if qid in subvols or qid == 5:
            active[qid] = tuple(f[1:])
            continue
        if f[1:3] != ["0.00B", "0.00B"] or f[5:] != ["---", "---"]:
            raise RuntimeError("unverified candidate: " + line)
        if f[3:5] == ["none", "none"]:
            unlimited.append(qid)
        elif f[3:5] == ["1.00TiB", "none"]:
            limited.append(qid)
        else:
            raise RuntimeError("unrecognized candidate limits: " + line)
    if set(active) != subvols | {5}:
        raise RuntimeError("active qgroup set mismatch")
    if len(seen) != len(active) + len(unlimited) + len(limited):
        raise RuntimeError("qgroup count mismatch")
    return subvols, active, unlimited, limited, seen


def stable_active(inv):
    """Compare live identity, limits, and relationships; ignore mutable usage.

    qgroup show -pcre fields: rfer, excl, max_rfer, max_excl, parent, child.
    """
    subvolumes, active = inv[:2]
    return (frozenset(subvolumes), {
        qid: fields[2:] for qid, fields in active.items()
    })


def protect(inv):
    subvols, active = inv[:2]
    for stamp, (id_, expected) in PROTECTED.items():
        if id_ not in subvols or id_ not in active:
            raise RuntimeError("protected qgroup absent: " + stamp)
        path = f"/@data/mars-received/@data/{stamp}"
        result = command("btrfs", "subvolume", "show", path)
        if field(result, "Subvolume ID") != str(id_) or field(result, "Received UUID") != expected:
            raise RuntimeError("protected identity mismatch: " + stamp)
        if command("btrfs", "property", "get", "-ts", path, "ro").strip() != "ro=true":
            raise RuntimeError("protected subvolume not readonly: " + stamp)


def summary(inv):
    return (len(inv[2]), len(inv[3]), len(inv[4]))


def event(file, name, **props):
    obj = {"utc": datetime.now(timezone.utc).isoformat(), "event": name, **props}
    file.write(json.dumps(obj, sort_keys=True) + "\n")
    file.flush()
    os.fsync(file.fileno())


def planned(inv, n):
    # Alternate quotas as available, and keep the selection deterministic.
    u, l = inv[2], inv[3]
    targets = []
    ui = li = 0
    while len(targets) < n and (ui < len(u) or li < len(l)):
        if ui < len(u) and len(targets) < n:
            targets.append(("unlimited", u[ui])); ui += 1
        if li < len(l) and len(targets) < n:
            targets.append(("limited", l[li])); li += 1
    if len(targets) != n:
        raise RuntimeError("insufficient candidates")
    return targets


def journal_data(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1:
        raise RuntimeError("unsafe or missing journal: " + str(path))
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        records = [json.loads(line) for line in raw.splitlines()]
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError("invalid journal: " + str(path)) from exc
    if not records:
        raise RuntimeError("empty journal: " + str(path))
    return records, digest


def reconciled_interruption(path, records, inv):
    """Validate the specific, previously investigated 675-removal interruption.

    This is intentionally NOT a generic bypass of arbitrary failed journals.
    """
    if path.name != "stage-c-20261021-201036Z-598228.jsonl":
        raise RuntimeError("journal not approved for reconciliation")
    if len(records) != 1352 or records[0].get("event") != "START":
        raise RuntimeError("unexpected interrupted journal structure")
    if records[-1].get("event") != "FAIL" or records[-1].get("error") != "active set changed":
        raise RuntimeError("unexpected interrupted journal outcome")
    start = records[0]
    if start.get("filesystem_uuid") != UUID or start.get("baseline") != [15414, 13901, 29449]:
        raise RuntimeError("journal baseline mismatch")
    targets = start.get("targets")
    if not isinstance(targets, list) or len(targets) != 1000 or len(set(targets)) != 1000:
        raise RuntimeError("invalid journal target list")
    attempts = [r.get("id") for r in records if r.get("event") == "ATTEMPT"]
    removed = [r.get("id") for r in records if r.get("event") == "REMOVED"]
    if (len(attempts) != 675 or len(removed) != 675 or attempts != removed
            or len(set(removed)) != 675 or targets[:675] != removed):
        raise RuntimeError("journal deletion sequence mismatch")
    if [r.get("event") for r in records] != (["START"] +
            [e for _ in range(675) for e in ("ATTEMPT", "REMOVED")] + ["FAIL"]):
        raise RuntimeError("journal event sequence mismatch")
    ids = {int(q.split("/")[1]) for q in removed if isinstance(q, str)
           and re.fullmatch(r"0/\d+", q)}
    if len(ids) != 675 or records[-1].get("completed") != [int(q.split("/")[1]) for q in removed]:
        raise RuntimeError("journal completion list mismatch")
    if ids & inv[4] or ids & inv[0] or any(qid in ids for qid, _ in PROTECTED.values()):
        raise RuntimeError("deleted IDs present or protected")
    if not inv[0] or not inv[0].issubset(inv[4]) or 5 not in inv[4]:
        raise RuntimeError("live subvolume/qgroup mismatch")
    if set(inv[1]) != inv[0] | {5}:
        raise RuntimeError("active qgroup set mismatch")
    return ids


def acknowledgement_path(journal):
    return journal.with_name(journal.name + ".ack.json")


def verify_acknowledgement(journal, records, digest, inv):
    acknowledgement = acknowledgement_path(journal)
    if not acknowledgement.is_file() or acknowledgement.is_symlink():
        raise RuntimeError("unresolved prior journal: " + str(journal))
    try:
        ack = json.loads(acknowledgement.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise RuntimeError("invalid acknowledgement: " + str(acknowledgement)) from exc
    if (ack.get("journal_sha256") != digest or ack.get("journal") != journal.name
            or ack.get("filesystem_uuid") != UUID or ack.get("removed") != 675
            or ack.get("reconciliation") != "verified-interrupted-675"):
        raise RuntimeError("acknowledgement mismatch: " + str(journal))
    reconciled_interruption(journal, records, inv)


def unresolved_journal(directory, inv=None):
    for path in sorted(directory.glob("stage-c-*.jsonl")):
        records, digest = journal_data(path)
        if records[-1].get("event") == "PASS":
            continue
        if inv is None:
            raise RuntimeError("unresolved prior journal: " + str(path))
        verify_acknowledgement(path, records, digest, inv)


def acknowledge(journal, expected_sha256, inv):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise RuntimeError("expected SHA-256 must have 64 lowercase hex characters")
    records, digest = journal_data(journal)
    if digest != expected_sha256:
        raise RuntimeError("journal SHA-256 mismatch")
    ids = reconciled_interruption(journal, records, inv)
    # The 2026-10-22 replication added a valid received snapshot (0/55815).
    # Candidate populations must remain at the reconciled baseline; a new
    # active subvolume contributes its own qgroup without becoming a candidate.
    if len(inv[2]) != 15076 or len(inv[3]) != 13564:
        raise RuntimeError("reconciled candidate baseline changed; independent review required")
    if len(inv[4]) != len(inv[0]) + 1 + 15076 + 13564:
        raise RuntimeError("reconciled qgroup population mismatch")
    path = acknowledgement_path(journal)
    if path.exists() or path.is_symlink():
        raise RuntimeError("acknowledgement already exists: " + str(path))
    obj = {
        "journal": journal.name,
        "journal_sha256": digest,
        "filesystem_uuid": UUID,
        "removed": len(ids),
        "live_total_at_acknowledgement": len(inv[4]),
        "reconciliation": "verified-interrupted-675",
        "utc": datetime.now(timezone.utc).isoformat(),
    }
    # Exclusive creation: the original journal remains unmodified.
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    directory_fd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    print("ACKNOWLEDGED:", path, "deleted IDs verified:", len(ids), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--acknowledge-journal", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--journal-dir", type=Path, default=DEFAULT_JOURNALS)
    args = parser.parse_args(argv)
    if args.acknowledge_journal:
        if args.batch_size is not None or not args.expected_sha256:
            parser.error("acknowledgement needs --expected-sha256 and no --batch-size")
    elif args.expected_sha256 or args.batch_size is None or not 1 <= args.batch_size <= 1000:
        parser.error("cleanup requires --batch-size 1..1000 and no --expected-sha256")
    if (args.apply or args.acknowledge_journal) and os.geteuid() != 0:
        parser.error("--apply requires root (sudo)")
    if not LOCK.is_file() or LOCK.is_symlink() or LOCK.stat().st_nlink != 1:
        raise RuntimeError("unsafe receiver lock")
    with LOCK.open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        environment()
        before = inventory()
        protect(before)
        if args.acknowledge_journal:
            if args.acknowledge_journal.parent.resolve() != args.journal_dir.resolve():
                raise RuntimeError("acknowledgement journal outside journal directory")
            acknowledge(args.acknowledge_journal, args.expected_sha256, before)
            return 0
        targets = planned(before, args.batch_size)
        print("Mode:", "APPLY" if args.apply else "DRY RUN", flush=True)
        print("Inventory:", summary(before), "targets:", len(targets), flush=True)
        print("First IDs:", " ".join("0/" + str(q) for _, q in targets[:10]), flush=True)
        if args.dry_run:
            return 0
        args.journal_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        unresolved_journal(args.journal_dir, before)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ-%f")
        path = args.journal_dir / f"stage-c-{stamp}.jsonl"
        completed = []
        with path.open("x", encoding="utf-8") as journal:
            try:
                event(journal, "START", filesystem_uuid=UUID, baseline=summary(before), targets=[f"0/{q}" for _, q in targets])
                for category, qid in targets:
                    # Every 25 deletions, detect independent metadata changes.
                    # The receiver flock prevents cooperating receiver writes, but
                    # cannot prevent unrelated root processes touching Btrfs.
                    if len(completed) % 25 == 0:
                        environment()
                        current = inventory()
                        if stable_active(current) != stable_active(before):
                            raise RuntimeError("active identity, limits or relationships changed")
                        if before[4] - current[4] != set(completed):
                            raise RuntimeError("unexpected qgroup changes")
                        if qid not in (current[2] if category == "unlimited" else current[3]):
                            raise RuntimeError("target no longer eligible")
                    event(journal, "ATTEMPT", id=f"0/{qid}", category=category)
                    subprocess.run(["btrfs", "qgroup", "destroy", f"0/{qid}", "/"], check=True, timeout=120)
                    completed.append(qid)
                    event(journal, "REMOVED", id=f"0/{qid}", category=category)
                    if len(completed) % 50 == 0:
                        print(f"Removed {len(completed)}/{len(targets)}", flush=True)
                environment()
                after = inventory()
                protect(after)
                if stable_active(after) != stable_active(before):
                    raise RuntimeError("active identity, limits or relationships changed")
                if before[4] - after[4] != set(completed):
                    raise RuntimeError("unexpected qgroup ID delta")
                if summary(after)[2] != summary(before)[2] - len(completed):
                    raise RuntimeError("unexpected post-batch count")
                event(journal, "PASS", removed=len(completed), final=summary(after))
                print("PASS; removed:", len(completed), "remaining:", len(after[2])+len(after[3]), flush=True)
            except BaseException as exc:
                event(journal, "FAIL", completed=completed, error=str(exc))
                print("STOP; journal:", path, "completed:", len(completed), flush=True)
                raise
        print("Journal:", path, flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.SubprocessError, OSError, AssertionError) as exc:
        print("STOP:", exc, file=sys.stderr)
        sys.exit(1)

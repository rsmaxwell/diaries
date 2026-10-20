#!/usr/bin/python3
"""Small timestamp-named Btrfs snapshot manager.

The manager owns only snapshots below the configured snapshot_root. It never
reads, renames or deletes Snapper's .snapshots/<number> hierarchy.

For Diaries-integrated backup hosts, create is additionally guarded by a
receiver-written verification marker and a shared writer lock. A snapshot can
therefore never be created while a managed receive is mutating the mirror, and
an unverified/mismatched Diaries mirror is rejected before snapshot creation.
"""

from __future__ import annotations

import argparse
import csv
import io
import fcntl
import hashlib
import json
import os
import socket
import stat
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

TIMESTAMP_FORMAT = "%Y%m%d-%H%M%SZ"
TIMESTAMP_RE = re.compile(r"^\d{8}-\d{6}Z$")


class SnapshotError(RuntimeError):
    pass


@dataclass(frozen=True)
class SnapshotSource:
    name: str
    source: Path


@dataclass(frozen=True)
class RetentionPolicy:
    hourly: int
    daily: int
    weekly: int
    monthly: int
    yearly: int
    minimum_age_minutes: int


@dataclass(frozen=True)
class VerificationPolicy:
    required: bool
    source_name: str
    dataset_relative_path: str
    marker_relative_path: str
    manifest_tool: Path | None


@dataclass(frozen=True)
class Config:
    snapshot_root: Path
    lock_path: Path
    writer_lock_path: Path | None
    sources: tuple[SnapshotSource, ...]
    retention: RetentionPolicy
    verification: VerificationPolicy
    replication_protection_required: bool = False
    replication_protection_file: Path | None = None
    checkpoint_holds_file: Path | None = None
    checkpoint_holds_required: bool = False


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        raise SnapshotError(
            "command failed (rc={}): {}\nstdout:\n{}\nstderr:\n{}".format(
                result.returncode,
                " ".join(command),
                result.stdout.rstrip(),
                result.stderr.rstrip(),
            )
        )
    return result


def positive_int(value: object, field: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SnapshotError(f"{field} must be an integer") from exc
    if number < 0:
        raise SnapshotError(f"{field} must not be negative")
    return number


def safe_relative(value: object, field: str, *, allow_empty: bool = False) -> str:
    if value in (None, "") and allow_empty:
        return ""
    if not isinstance(value, str) or not value:
        raise SnapshotError(f"{field} must be a non-empty relative path")
    if "\\" in value:
        raise SnapshotError(f"{field} must use '/' separators")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise SnapshotError(f"{field} must be a canonical relative path")
    canonical = path.as_posix()
    if canonical != value:
        raise SnapshotError(f"{field} must be a canonical relative path")
    return canonical


def load_config(path: Path) -> Config:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SnapshotError(f"cannot read configuration {path}: {exc}") from exc

    root = Path(raw["snapshot_root"]).resolve()
    lock_path = Path(raw.get("lock_path", "/run/lock/btrfs-snapshot-manager.lock"))
    writer_lock_raw = raw.get("writer_lock_path") or ""
    writer_lock_path = Path(writer_lock_raw) if writer_lock_raw else None
    if writer_lock_path is not None and not writer_lock_path.is_absolute():
        raise SnapshotError("writer_lock_path must be absolute when configured")

    sources: list[SnapshotSource] = []
    seen_names: set[str] = set()
    for item in raw.get("sources", []):
        name = str(item["name"])
        if not name or "/" in name or name in {".", ".."}:
            raise SnapshotError(f"invalid snapshot source name: {name!r}")
        if name in seen_names:
            raise SnapshotError(f"duplicate snapshot source name: {name}")
        seen_names.add(name)
        sources.append(SnapshotSource(name=name, source=Path(item["path"]).resolve()))

    if not sources:
        raise SnapshotError("configuration has no snapshot sources")

    retention = raw.get("retention", {})
    policy = RetentionPolicy(
        hourly=positive_int(retention.get("hourly", 0), "retention.hourly"),
        daily=positive_int(retention.get("daily", 0), "retention.daily"),
        weekly=positive_int(retention.get("weekly", 0), "retention.weekly"),
        monthly=positive_int(retention.get("monthly", 0), "retention.monthly"),
        yearly=positive_int(retention.get("yearly", 0), "retention.yearly"),
        minimum_age_minutes=positive_int(
            retention.get("minimum_age_minutes", 30), "retention.minimum_age_minutes"
        ),
    )

    verification_raw = raw.get("verification", {})
    required = bool(verification_raw.get("required", False))
    source_name = str(verification_raw.get("source_name", ""))
    dataset_relative_path = safe_relative(
        verification_raw.get("dataset_relative_path", ""),
        "verification.dataset_relative_path",
        allow_empty=not required,
    )
    marker_relative_path = safe_relative(
        verification_raw.get("marker_relative_path", ""),
        "verification.marker_relative_path",
        allow_empty=not required,
    )
    manifest_tool_raw = verification_raw.get("manifest_tool") or ""
    manifest_tool = Path(manifest_tool_raw) if manifest_tool_raw else None
    if manifest_tool is not None and not manifest_tool.is_absolute():
        raise SnapshotError("verification.manifest_tool must be absolute when configured")
    if required:
        if source_name not in seen_names:
            raise SnapshotError("verification.source_name must name a configured snapshot source")
        if writer_lock_path is None:
            raise SnapshotError("writer_lock_path is required when Diaries verification is required")

    verification = VerificationPolicy(
        required=required,
        source_name=source_name,
        dataset_relative_path=dataset_relative_path,
        marker_relative_path=marker_relative_path,
        manifest_tool=manifest_tool,
    )
    return Config(
        snapshot_root=root,
        lock_path=lock_path,
        writer_lock_path=writer_lock_path,
        sources=tuple(sources),
        retention=policy,
        verification=verification,
        replication_protection_required=bool(raw.get("replication_protection", {}).get("required", False)),
        replication_protection_file=Path(raw.get("replication_protection", {}).get("path", str(root / ".replication-protection.json"))),
        checkpoint_holds_file=Path(raw.get("checkpoint_holds", {}).get("path", str(root / ".checkpoint-holds.json"))),
        checkpoint_holds_required=bool(raw.get("checkpoint_holds", {}).get("required", False)),
    )


def require_root() -> None:
    if os.geteuid() != 0:
        raise SnapshotError("this command must run as root")


def filesystem_type(path: Path) -> str:
    result = run(["findmnt", "-T", str(path), "-n", "-o", "FSTYPE"])
    value = result.stdout.strip()
    if not value:
        raise SnapshotError(f"could not determine filesystem type for {path}")
    return value


def require_btrfs(path: Path) -> None:
    fstype = filesystem_type(path)
    if fstype != "btrfs":
        raise SnapshotError(f"{path} is on {fstype}, expected btrfs")


def require_subvolume(path: Path) -> None:
    result = run(["btrfs", "subvolume", "show", str(path)], check=False)
    if result.returncode != 0:
        raise SnapshotError(f"{path} is not an accessible Btrfs subvolume")


def source_directory(config: Config, source: SnapshotSource) -> Path:
    return config.snapshot_root / source.name


def snapshot_path(config: Config, source: SnapshotSource, timestamp: str) -> Path:
    return source_directory(config, source) / timestamp


def source_by_name(config: Config, name: str) -> SnapshotSource:
    for source in config.sources:
        if source.name == name:
            return source
    raise SnapshotError(f"configured snapshot source not found: {name}")


def path_within(root: Path, relative: str) -> Path:
    return root.joinpath(*PurePosixPath(relative).parts)


def resolved_inside(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    root_resolved = root.resolve(strict=True)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SnapshotError(f"{label} escapes managed source {root_resolved}: {resolved}") from exc
    return resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_verified_diaries(config: Config, *, strict: bool) -> dict[str, object] | None:
    verification = config.verification
    if not verification.required:
        return None
    source = source_by_name(config, verification.source_name)
    marker_path = path_within(source.source, verification.marker_relative_path)
    dataset_path = path_within(source.source, verification.dataset_relative_path)
    try:
        if marker_path.is_symlink() or not marker_path.is_file():
            raise SnapshotError(f"verified Diaries marker missing/unsafe: {marker_path}")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if not isinstance(marker, dict):
            raise SnapshotError("verified Diaries marker must be a JSON object")
        if marker.get("state") != "verified-published" or marker.get("snapshotEligible") is not True:
            raise SnapshotError("Diaries marker is not snapshot eligible")
        if marker.get("datasetRelativePath") != verification.dataset_relative_path:
            raise SnapshotError("Diaries marker datasetRelativePath does not match manager configuration")
        backup_id = marker.get("backupId")
        logical_dataset = marker.get("logicalDataset")
        manifest_hash = marker.get("manifestSha256")
        if not isinstance(backup_id, str) or not backup_id:
            raise SnapshotError("Diaries marker has no valid backupId")
        if not isinstance(logical_dataset, str) or not logical_dataset:
            raise SnapshotError("Diaries marker has no valid logicalDataset")
        if not isinstance(manifest_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", manifest_hash):
            raise SnapshotError("Diaries marker has no valid manifestSha256")

        resolved_dataset = resolved_inside(dataset_path, source.source, "Diaries dataset")
        manifest_path = resolved_dataset / "dataset-manifest.json"
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise SnapshotError(f"Diaries manifest missing/unsafe: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise SnapshotError("Diaries manifest must be a JSON object")
        if manifest.get("backupId") != backup_id or manifest.get("logicalDataset") != logical_dataset:
            raise SnapshotError("Diaries marker identity does not match current manifest")
        actual_hash = sha256_file(manifest_path)
        if actual_hash != manifest_hash:
            raise SnapshotError("Diaries marker manifestSha256 does not match current manifest")
        return {
            "backupId": backup_id,
            "logicalDataset": logical_dataset,
            "manifestSha256": actual_hash,
            "marker": str(marker_path),
            "dataset": str(dataset_path),
        }
    except (OSError, ValueError, json.JSONDecodeError, SnapshotError) as exc:
        if strict:
            if isinstance(exc, SnapshotError):
                raise
            raise SnapshotError(f"cannot validate verified Diaries state: {exc}") from exc
        return {"error": str(exc)}


def preflight(config: Config) -> None:
    if not config.snapshot_root.exists():
        raise SnapshotError(f"snapshot root does not exist: {config.snapshot_root}")
    require_btrfs(config.snapshot_root)
    require_subvolume(config.snapshot_root)

    root_device = run(["findmnt", "-T", str(config.snapshot_root), "-n", "-o", "UUID"]).stdout.strip()
    if not root_device:
        raise SnapshotError(f"could not determine Btrfs filesystem UUID for {config.snapshot_root}")
    for source in config.sources:
        if not source.source.exists():
            raise SnapshotError(f"snapshot source does not exist: {source.source}")
        require_btrfs(source.source)
        require_subvolume(source.source)
        source_device = run(["findmnt", "-T", str(source.source), "-n", "-o", "UUID"]).stdout.strip()
        if not source_device:
            raise SnapshotError(f"could not determine Btrfs filesystem UUID for {source.source}")
        if source_device != root_device:
            raise SnapshotError(
                f"snapshot source {source.source} and repository {config.snapshot_root} "
                f"are not on the same Btrfs filesystem ({source_device!r} != {root_device!r})"
            )
        directory = source_directory(config, source)
        if not directory.is_dir():
            raise SnapshotError(f"snapshot destination directory does not exist: {directory}")

    if config.verification.required:
        source = source_by_name(config, config.verification.source_name)
        dataset_parent = path_within(source.source, config.verification.dataset_relative_path).parent
        marker_parent = path_within(source.source, config.verification.marker_relative_path).parent
        for label, parent in (("dataset", dataset_parent), ("marker", marker_parent)):
            if not parent.exists() or not parent.is_dir() or parent.is_symlink():
                raise SnapshotError(f"verified Diaries {label} parent missing/unsafe: {parent}")
        if config.writer_lock_path is None:
            raise SnapshotError("verified Diaries integration requires writer_lock_path")
        if config.writer_lock_path.parent != marker_parent:
            raise SnapshotError(
                "writer_lock_path must share the verified marker parent so receiver and snapshot manager "
                "coordinate the same whole-backup tree"
            )


def now_timestamp() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


def parse_timestamp(name: str) -> datetime:
    if not TIMESTAMP_RE.match(name):
        raise ValueError(name)
    return datetime.strptime(name, TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)


def create_all(config: Config, timestamp: str | None = None) -> str:
    preflight(config)
    verification = read_verified_diaries(config, strict=True)
    if verification is not None:
        print(
            "VERIFIED-DIARIES "
            f"{verification['logicalDataset']} {verification['backupId']} "
            f"manifest={verification['manifestSha256']}"
        )
    stamp = timestamp or now_timestamp()
    try:
        parse_timestamp(stamp)
    except ValueError as exc:
        raise SnapshotError(f"invalid UTC snapshot timestamp: {stamp}") from exc

    destinations = [snapshot_path(config, source, stamp) for source in config.sources]
    existing = [path for path in destinations if path.exists()]
    if existing:
        raise SnapshotError(f"snapshot timestamp already exists: {stamp}: {existing}")

    created: list[Path] = []
    try:
        for source, destination in zip(config.sources, destinations):
            print(f"CREATE {source.name}: {source.source} -> {destination}")
            run(["btrfs", "subvolume", "snapshot", "-r", str(source.source), str(destination)])
            created.append(destination)
    except Exception:
        for destination in reversed(created):
            print(f"ROLLBACK {destination}", file=sys.stderr)
            run(["btrfs", "subvolume", "delete", str(destination)], check=False)
        raise

    print(f"Created timestamp set {stamp} ({len(created)} snapshots)")
    return stamp


def list_managed(config: Config, source: SnapshotSource) -> list[tuple[str, datetime, Path]]:
    directory = source_directory(config, source)
    snapshots: list[tuple[str, datetime, Path]] = []
    if not directory.exists():
        return snapshots
    for item in directory.iterdir():
        if not item.is_dir() or not TIMESTAMP_RE.match(item.name):
            continue
        try:
            dt = parse_timestamp(item.name)
        except ValueError:
            continue
        snapshots.append((item.name, dt, item))
    snapshots.sort(key=lambda entry: entry[1], reverse=True)
    return snapshots


def managed_snapshot_sets(config: Config) -> tuple[list[tuple[str, datetime]], dict[str, set[str]]]:
    by_timestamp: dict[str, set[str]] = {}
    dates: dict[str, datetime] = {}
    for source in config.sources:
        for name, dt, _ in list_managed(config, source):
            by_timestamp.setdefault(name, set()).add(source.name)
            dates[name] = dt
    complete_names = {source.name for source in config.sources}
    complete: list[tuple[str, datetime]] = []
    incomplete: dict[str, set[str]] = {}
    for name, present in by_timestamp.items():
        if present == complete_names:
            complete.append((name, dates[name]))
        else:
            incomplete[name] = present
    complete.sort(key=lambda row: row[1], reverse=True)
    return complete, incomplete


def bucket_hour(dt: datetime) -> tuple[int, int, int, int]:
    return dt.year, dt.month, dt.day, dt.hour


def bucket_day(dt: datetime) -> tuple[int, int, int]:
    return dt.year, dt.month, dt.day


def bucket_week(dt: datetime) -> tuple[int, int]:
    iso = dt.isocalendar()
    return iso.year, iso.week


def bucket_month(dt: datetime) -> tuple[int, int]:
    return dt.year, dt.month


def bucket_year(dt: datetime) -> tuple[int]:
    return (dt.year,)


def add_bucket_keeps(
    snapshots: Iterable[tuple[str, datetime, Path]],
    keep: set[str],
    limit: int,
    bucket: Callable[[datetime], tuple],
) -> None:
    if limit <= 0:
        return
    buckets: set[tuple] = set()
    for name, dt, _ in snapshots:
        key = bucket(dt)
        if key in buckets:
            continue
        buckets.add(key)
        keep.add(name)
        if len(buckets) >= limit:
            return


def retention_keep_set(
    snapshots: list[tuple[str, datetime, Path]], policy: RetentionPolicy, now: datetime
) -> set[str]:
    if not snapshots:
        return set()

    keep: set[str] = {snapshots[0][0]}
    minimum_age_seconds = policy.minimum_age_minutes * 60
    for name, dt, _ in snapshots:
        if (now - dt).total_seconds() < minimum_age_seconds:
            keep.add(name)

    add_bucket_keeps(snapshots, keep, policy.hourly, bucket_hour)
    add_bucket_keeps(snapshots, keep, policy.daily, bucket_day)
    add_bucket_keeps(snapshots, keep, policy.weekly, bucket_week)
    add_bucket_keeps(snapshots, keep, policy.monthly, bucket_month)
    add_bucket_keeps(snapshots, keep, policy.yearly, bucket_year)
    return keep



def replication_pins(config: Config) -> set[str]:
    """Fail closed when replication protection is enabled; never prune unvalidated state."""
    if not config.replication_protection_required:
        return set()
    path = config.replication_protection_file
    if path is None or not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise SnapshotError("Replication protection state absent or unsafe; pruning prohibited")
    import stat
    metadata = path.stat()
    if metadata.st_uid != 0 or metadata.st_mode & 0o022:
        raise SnapshotError("Replication protection file must be root-owned and non-writable by others")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("schema") != 1 or not isinstance(state.get("protected"), dict):
            raise ValueError("Invalid protection schema")
        pins = state["protected"]
        if any(not re.fullmatch(r"[0-9]{8}-[0-9]{6}Z", stamp) or
               not isinstance(uuid, str) or not re.fullmatch(r"[0-9a-f-]{36}", uuid)
               for stamp, uuid in pins.items()):
            raise ValueError("Invalid pinned snapshot")
        return set(pins)
    except (ValueError, OSError, TypeError) as exc:
        raise SnapshotError(f"Unsafe replication protection: {exc}") from exc



def read_checkpoint_holds(config: Config) -> dict[str, dict[str, str]]:
    """Independently held recovery checkpoints. Invalid/missing enabled state blocks pruning."""
    if not config.checkpoint_holds_required:
        return {}
    path = config.checkpoint_holds_file
    if path is None or not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise SnapshotError("Checkpoint hold state absent or unsafe; pruning prohibited")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_uid != 0 or metadata.st_mode & 0o077:
        raise SnapshotError("Checkpoint hold file must be regular, root-owned and mode 0600")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or set(raw) != {"schema", "holds"} or raw["schema"] != 1 or not isinstance(raw["holds"], dict):
            raise ValueError("invalid checkpoint hold schema")
        for stamp, record in raw["holds"].items():
            if not TIMESTAMP_RE.fullmatch(stamp) or not isinstance(record, dict) or set(record) != {"reason", "source_uuids"}:
                raise ValueError("invalid hold entry")
            if not isinstance(record["reason"], str) or not record["reason"].strip() or len(record["reason"]) > 256:
                raise ValueError("invalid hold reason")
            if not isinstance(record["source_uuids"], dict) or set(record["source_uuids"]) != {s.name for s in config.sources}:
                raise ValueError("invalid hold source list")
            if any(not isinstance(u, str) or not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", u)
                   for u in record["source_uuids"].values()):
                raise ValueError("invalid hold UUID")
        return raw["holds"]
    except (ValueError, OSError, TypeError) as exc:
        raise SnapshotError(f"Unsafe checkpoint hold state: {exc}") from exc


def write_checkpoint_holds(config: Config, holds: dict[str, dict[str, str]]) -> None:
    path = config.checkpoint_holds_file
    if path is None:
        raise SnapshotError("checkpoint hold file not configured")
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix=".checkpoint-holds-", dir=str(path.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump({"schema": 1, "holds": holds}, out, indent=2, sort_keys=True)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def checkpoint_command(config: Config, command: str, timestamp: str | None, reason: str | None) -> None:
    if not config.checkpoint_holds_required:
        raise SnapshotError("checkpoint holds not enabled for this host")
    holds = read_checkpoint_holds(config)
    if command == "hold-list":
        for stamp, record in sorted(holds.items()):
            print(f"HELD {stamp} reason={record['reason']}")
        return
    assert timestamp is not None
    parse_timestamp(timestamp)
    if command == "hold-add":
        if timestamp in holds:
            raise SnapshotError("checkpoint already held; release explicitly before changing reason")
        if not reason or not reason.strip() or len(reason) > 256:
            raise SnapshotError("hold-add requires a reason (1-256 characters)")
        source_uuids = {}
        for source in config.sources:
            target = snapshot_path(config, source, timestamp)
            require_subvolume(target)
            result = run(["btrfs", "subvolume", "show", str(target)]).stdout
            match = re.search(r"^\s*UUID:\s*([0-9a-f-]{36})\s*$", result, re.M)
            if not match or not re.search(r"^\s*Flags:\s*readonly\s*$", result, re.M):
                raise SnapshotError(f"held snapshot must exist and be read-only: {target}")
            source_uuids[source.name] = match.group(1)
        holds[timestamp] = {"reason": reason.strip(), "source_uuids": source_uuids}
        write_checkpoint_holds(config, holds)
        print(f"HELD: {timestamp}")
    elif command == "hold-release":
        if timestamp not in holds:
            raise SnapshotError("checkpoint has no hold")
        # Never permit release of the active replication parent via the hold CLI.
        if timestamp in replication_pins(config):
            raise SnapshotError("cannot release a checkpoint while it is the protected replication parent")
        del holds[timestamp]
        write_checkpoint_holds(config, holds)
        print(f"RELEASED: {timestamp}")

def validate_prune_candidate(config: Config, source: SnapshotSource, timestamp: str) -> None:
    """Refuse unmanaged paths, symlinks, writable snapshots and non-subvolumes."""
    if not TIMESTAMP_RE.fullmatch(timestamp):
        raise SnapshotError(f"invalid managed timestamp: {timestamp}")
    candidate = snapshot_path(config, source, timestamp)
    parent = source_directory(config, source)
    if parent.is_symlink() or candidate.is_symlink() or not candidate.is_dir():
        raise SnapshotError(f"unsafe prune candidate: {candidate}")
    if candidate.parent.resolve(strict=True) != parent.resolve(strict=True):
        raise SnapshotError(f"candidate outside managed source: {candidate}")
    require_subvolume(candidate)
    flags = run(["btrfs", "property", "get", "-ts", str(candidate), "ro"]).stdout.strip()
    if flags != "ro=true":
        raise SnapshotError(f"refusing writable snapshot deletion: {candidate}: {flags}")


def prune(config: Config, dry_run: bool = False) -> int:
    preflight(config)
    complete, incomplete = managed_snapshot_sets(config)
    if incomplete:
        detail = ", ".join(f"{stamp}:{sorted(names)}" for stamp, names in sorted(incomplete.items()))
        raise SnapshotError(f"refusing retention with incomplete timestamp sets: {detail}")
    now = datetime.now(timezone.utc)
    synthetic = [(name, dt, config.snapshot_root / name) for name, dt in complete]
    keep = retention_keep_set(synthetic, config.retention, now)
    pins = replication_pins(config)
    keep.update(pins)
    holds = read_checkpoint_holds(config)
    keep.update(holds)
    if holds:
        print(f"CHECKPOINT-HELD: {sorted(holds)}")
    if pins:
        print(f"REPLICATION-PROTECTED: {sorted(pins)}")
    # Validate the *entire* deletion plan before touching any snapshot in a set.
    # In particular, do not delete one half of a root/@data pair if its peer is unsafe.
    candidates = [(name, source) for name, _ in complete if name not in keep for source in config.sources]
    for name, source in candidates:
        validate_prune_candidate(config, source, name)
    deleted_sets = 0
    print(f"RETENTION sets: total={len(complete)} keep={len(keep)} sources={len(config.sources)}")
    for name, _ in complete:
        if name in keep:
            continue
        deleted_sets += 1
        if dry_run:
            for source in config.sources:
                print(f"WOULD-DELETE {source.name} {name} {snapshot_path(config, source, name)}")
            continue
        for source in reversed(config.sources):
            path = snapshot_path(config, source, name)
            print(f"DELETE {source.name} {name} {path}")
            run(["btrfs", "subvolume", "delete", str(path)])
    print(("Would delete" if dry_run else "Deleted") + f" {deleted_sets} complete timestamp sets")
    return deleted_sets


def legacy_snapper_inventory(config: Config, mappings: list[str]) -> dict[str, list[dict[str, object]]]:
    """Read legacy snapshots only; explicit mappings and identical canonical source required."""
    if not mappings:
        raise SnapshotError("legacy-plan needs at least one --legacy-map SOURCE=SNAPPER_CONFIG")
    result: dict[str, list[dict[str, object]]] = {}
    used_configs: set[str] = set()
    for mapping in mappings:
        if mapping.count("=") != 1:
            raise SnapshotError(f"invalid legacy mapping: {mapping!r}")
        source_name, snapper_config = mapping.split("=", 1)
        if not re.fullmatch(r"[A-Za-z0-9_@.-]+", snapper_config) or snapper_config in used_configs:
            raise SnapshotError(f"unsafe or duplicate Snapper config: {snapper_config!r}")
        used_configs.add(snapper_config)
        source = source_by_name(config, source_name)
        raw_config = run(["snapper", "-c", snapper_config, "get-config"]).stdout
        match = re.search(r"^\s*SUBVOLUME\s*\|\s*(.*?)\s*$", raw_config, re.MULTILINE)
        if not match or not match.group(1).startswith("/"):
            raise SnapshotError(f"cannot verify SUBVOLUME for Snapper config {snapper_config}")
        subvolume = Path(match.group(1))
        if subvolume.is_symlink() or subvolume.resolve(strict=True) != source.source.resolve(strict=True):
            raise SnapshotError(f"Snapper {snapper_config} SUBVOLUME does not match {source_name}")
        require_btrfs(subvolume)
        require_subvolume(subvolume)
        snapshots_root = subvolume / ".snapshots"
        output = run(["snapper", "--csvout", "--iso", "-c", snapper_config, "list"]).stdout
        rows = list(csv.DictReader(io.StringIO(output)))
        if not rows or not rows[0]:
            raise SnapshotError(f"empty or unreadable Snapper CSV: {snapper_config}")
        normalized = [{str(k).strip().lower().replace(" ", "_"): str(v or "").strip()
                       for k, v in row.items() if k is not None} for row in rows]
        # Snapper CSV versions use either '#' or 'number' for the snapshot ID.
        # Require exactly one of them rather than accepting an ambiguous header.
        columns = set(normalized[0])
        required = {"type", "date", "cleanup"}
        number_columns = columns & {"#", "number"}
        if not required.issubset(columns) or len(number_columns) != 1:
            raise SnapshotError(f"unexpected Snapper CSV columns: {sorted(columns)}")
        number_column = next(iter(number_columns))
        # An empty Snapper configuration can legitimately have no .snapshots
        # directory. Never relax the directory check for numbered snapshots.
        # Reject symlinks even in the empty case.
        if snapshots_root.is_symlink():
            raise SnapshotError(f"unsafe Snapper snapshot root: {snapshots_root}")
        records: list[dict[str, object]] = []
        seen: set[int] = set()
        for row in normalized:
            try:
                number = int(row[number_column])
            except ValueError as exc:
                raise SnapshotError(f"invalid Snapper snapshot number {row[number_column]!r}") from exc
            if number == 0:
                continue
            if number < 0 or number in seen:
                raise SnapshotError(f"duplicate/invalid Snapper number: {number}")
            if not snapshots_root.is_dir():
                raise SnapshotError(f"unsafe Snapper snapshot root: {snapshots_root}")
            seen.add(number)
            kind, cleanup = row["type"].lower(), row["cleanup"].lower()
            date = row["date"]
            try:
                dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    # Snapper --csvout --iso can omit an offset.  Only assign UTC
                    # when the host timezone is explicitly configured as UTC.
                    # Checking the system configuration (not the Python process
                    # TZ environment) avoids silent bucket misclassification.
                    host_timezone = run(["timedatectl", "show", "-p", "Timezone", "--value"]).stdout.strip()
                    if host_timezone not in {"UTC", "Etc/UTC"}:
                        raise SnapshotError(
                            f"timezone-less Snapper date for {number} requires verified UTC host; "
                            f"configured timezone: {host_timezone!r}")
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone.utc)
            except ValueError as exc:
                raise SnapshotError(f"unparseable Snapper date {date!r} for {number}") from exc
            path = snapshots_root / str(number) / "snapshot"
            if path.is_symlink() or not path.is_dir():
                raise SnapshotError(f"missing or unsafe Snapper snapshot {path}")
            require_subvolume(path)
            ro = run(["btrfs", "property", "get", "-ts", str(path), "ro"]).stdout.strip()
            if ro != "ro=true":
                raise SnapshotError(f"Snapper snapshot is not read-only: {path}")
            records.append({"source": source_name, "config": snapper_config, "number": number,
                            "timestamp": dt, "kind": kind, "cleanup": cleanup,
                            "description": row.get("description", ""), "path": str(path)})
        result[source_name] = records
    return result


def legacy_plan(config: Config, mappings: list[str], output_json: bool, emit: bool = True) -> dict[str, object]:
    """Emit a non-authoritative read-only plan; never invoked by prune/run."""
    preflight(config)
    complete, incomplete = managed_snapshot_sets(config)
    if incomplete:
        raise SnapshotError(f"incomplete native snapshot sets: {sorted(incomplete)}")
    pins = replication_pins(config)
    holds = read_checkpoint_holds(config)
    now = datetime.now(timezone.utc)
    native_rows = [(name, dt, config.snapshot_root / name) for name, dt in complete]
    native_keep = retention_keep_set(native_rows, config.retention, now) | pins | set(holds)
    legacy = legacy_snapper_inventory(config, mappings)
    tiers = (("hourly", config.retention.hourly, bucket_hour),
             ("daily", config.retention.daily, bucket_day),
             ("weekly", config.retention.weekly, bucket_week),
             ("monthly", config.retention.monthly, bucket_month),
             ("yearly", config.retention.yearly, bucket_year))
    decisions: list[dict[str, object]] = []
    for source_name, records in sorted(legacy.items()):
        eligible = [r for r in records if r["kind"] == "single" and r["cleanup"] == "timeline"]
        anchor = max(eligible, key=lambda r: (r["timestamp"], r["number"])) if eligible else None
        reasons: dict[int, list[str]] = {int(r["number"]): [] for r in eligible}
        for tier, limit, bucket_fn in tiers:
            if not limit:
                continue
            anchors = [(dt, None) for name, dt in complete if name in native_keep]
            entries = anchors + [(r["timestamp"], r) for r in eligible]
            # Select newest populated buckets, then prefer any native keeper within
            # each bucket even if its timestamp is earlier than a legacy member.
            grouped: dict[tuple, list[tuple[datetime, dict[str, object] | None]]] = {}
            for timestamp, rec in entries:
                grouped.setdefault(bucket_fn(timestamp), []).append((timestamp, rec))
            buckets = sorted(grouped, key=lambda key: max(dt for dt, _ in grouped[key]), reverse=True)
            for bucket in buckets[:limit]:
                choices = grouped[bucket]
                if any(rec is None for _, rec in choices):
                    continue
                _, winner = max(choices, key=lambda pair: (pair[0], int(pair[1]["number"])))
                reasons[int(winner["number"])].append(f"GFS_{tier.upper()}:{'-'.join(map(str, bucket))}")
        for rec in sorted(records, key=lambda r: int(r["number"])):
            number = int(rec["number"])
            reason = list(reasons.get(number, []))
            if rec not in eligible:
                decision = "EXCLUDED"
                reason = ["NON_TIMELINE_OR_NON_SINGLE"]
            else:
                if rec is anchor:
                    reason.append("LATEST_LEGACY_ANCHOR")
                if (now - rec["timestamp"]).total_seconds() < config.retention.minimum_age_minutes * 60:
                    reason.append("MINIMUM_AGE")
                decision = "KEEP" if reason else "WOULD-DELETE"
            decisions.append({"source": source_name, "config": rec["config"],
                              "number": number, "timestamp_utc": rec["timestamp"].isoformat(),
                              "decision": decision, "reasons": reason})
    document = {"mode": "READ_ONLY", "authorizes_deletion": False,
                "generated_at_utc": now.isoformat(), "native_complete": len(complete),
                "native_keepers": sorted(native_keep), "decisions": decisions}
    if emit and output_json:
        print(json.dumps(document, indent=2, sort_keys=True))
    elif emit:
        print(f"LEGACY PLAN READ-ONLY native={len(complete)} native_keep={len(native_keep)}")
        for entry in decisions:
            print(f"{entry['decision']:12} {entry['source']:8} {entry['config']:12} "
                  f"{entry['number']:>8} {entry['timestamp_utc']} "
                  f"{','.join(entry['reasons'])}")
        print("NO DELETION AUTHORISED")
    return document



def legacy_delete(config: Config, approval_path: Path, source: str, snapper_config: str,
                  number: int, execute: bool) -> None:
    """One exact, gated legacy deletion; never used by native prune/run."""
    if not execute:
        raise SnapshotError("legacy deletion requires explicit --execute")
    if number <= 0 or not re.fullmatch(r"[A-Za-z0-9_@.-]+", snapper_config):
        raise SnapshotError("invalid legacy snapshot ID/config")
    # A root-owned, non-symlink, non-group/world-writable policy is mandatory.
    if approval_path.is_symlink():
        raise SnapshotError("legacy approval file must not be a symlink")
    st = approval_path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or st.st_mode & 0o022:
        raise SnapshotError("legacy approval file must be root-owned and not group/world-writable")
    policy = json.loads(approval_path.read_text(encoding="utf-8"))
    if (not isinstance(policy, dict) or policy.get("enabled") is not True or
            policy.get("allow_delete") is not True or
            policy.get("host") != socket.gethostname() or
            policy.get("source") != source or policy.get("snapper_config") != snapper_config or
            policy.get("snapshot_id") != number or type(policy.get("snapshot_id")) is not int):
        raise SnapshotError("legacy deletion not authorised for exact host/source/config/ID")
    mappings = [f"{source}={snapper_config}"]
    # Establish the precise candidate and its identity before any mutation.
    initial = legacy_plan(config, mappings, False, emit=False)
    matches = [r for r in initial["decisions"] if r["source"] == source and
               r["config"] == snapper_config and r["number"] == number]
    if len(matches) != 1 or matches[0]["decision"] != "WOULD-DELETE":
        raise SnapshotError("snapshot is not a unique WOULD-DELETE candidate")
    original = matches[0]
    # Check again immediately before deletion, with a fresh inventory and
    # native protections (including pins and holds). Fail closed on any change.
    current = legacy_plan(config, mappings, False, emit=False)
    refreshed = [r for r in current["decisions"] if r["source"] == source and
                 r["config"] == snapper_config and r["number"] == number]
    if len(refreshed) != 1 or refreshed[0] != original or refreshed[0]["decision"] != "WOULD-DELETE":
        raise SnapshotError("legacy candidate identity or retention decision changed")
    print(f"LEGACY DELETE approved host={socket.gethostname()} source={source} "
          f"config={snapper_config} id={number} timestamp={original['timestamp_utc']}")
    run(["snapper", "-c", snapper_config, "delete", str(number)])
    print(f"LEGACY DELETE completed config={snapper_config} id={number}")


def show_list(config: Config) -> None:
    complete, incomplete = managed_snapshot_sets(config)
    print("TIMESTAMP          STATE      SOURCES")
    for name, _ in complete:
        print(f"{name:18} COMPLETE   {','.join(source.name for source in config.sources)}")
    for name in sorted(incomplete, reverse=True):
        print(f"{name:18} INCOMPLETE {','.join(sorted(incomplete[name]))}")


def show_status(config: Config) -> None:
    preflight(config)
    complete, incomplete = managed_snapshot_sets(config)
    print(f"snapshot_root={config.snapshot_root}")
    print(f"filesystem={filesystem_type(config.snapshot_root)}")
    print(
        "retention="
        f"hourly:{config.retention.hourly},daily:{config.retention.daily},"
        f"weekly:{config.retention.weekly},monthly:{config.retention.monthly},"
        f"yearly:{config.retention.yearly},minimum_age_minutes:{config.retention.minimum_age_minutes}"
    )
    print(f"complete_timestamp_sets={len(complete)};incomplete_timestamp_sets={len(incomplete)}")
    for source in config.sources:
        print(f"source={source.name}:{source.source};managed_snapshots={len(list_managed(config, source))}")
    if config.verification.required:
        state = read_verified_diaries(config, strict=False)
        if state and "error" not in state:
            print(
                "diaries_verification=valid;"
                f"logicalDataset={state['logicalDataset']};backupId={state['backupId']};"
                f"marker={state['marker']}"
            )
        else:
            print(f"diaries_verification=not-ready;detail={(state or {}).get('error', 'unknown')}")
    else:
        print("diaries_verification=disabled")


def with_lock(path: Path, *, shared: bool = False, nonblocking: bool = True,
              require_existing: bool = False):
    if not require_existing:
        path.parent.mkdir(parents=True, exist_ok=True)
    flags_open = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC
    if not require_existing:
        flags_open |= os.O_CREAT
    fd = os.open(path, flags_open, 0o600)
    handle = os.fdopen(fd, "r+")
    if require_existing:
        details = os.fstat(fd)
        if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
            handle.close()
            raise SnapshotError(f"unsafe existing writer lock: {path}")
    flags = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
    if nonblocking:
        flags |= fcntl.LOCK_NB
    try:
        fcntl.flock(handle.fileno(), flags)
    except BlockingIOError as exc:
        handle.close()
        raise SnapshotError(f"another operation holds {path}") from exc
    return handle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/etc/btrfs-snapshot-manager.json")
    sub = parser.add_subparsers(dest="command", required=True)
    create_parser = sub.add_parser("create")
    create_parser.add_argument("--timestamp")
    prune_parser = sub.add_parser("prune")
    prune_parser.add_argument("--dry-run", action="store_true")
    sub.add_parser("list")
    sub.add_parser("status")
    legacy_parser = sub.add_parser("legacy-plan", help="read-only legacy Snapper retention planning")
    legacy_parser.add_argument("--legacy-map", action="append", default=[], metavar="SOURCE=CONFIG")
    legacy_parser.add_argument("--json", action="store_true")
    delete_parser = sub.add_parser("legacy-delete", help="single-ID explicitly approved Snapper deletion")
    delete_parser.add_argument("--approval-file", required=True)
    delete_parser.add_argument("--source", required=True)
    delete_parser.add_argument("--snapper-config", required=True)
    delete_parser.add_argument("--snapshot-id", type=int, required=True)
    delete_parser.add_argument("--execute", action="store_true")
    sub.add_parser("run")
    add_parser = sub.add_parser("hold-add")
    add_parser.add_argument("timestamp")
    add_parser.add_argument("--reason", required=True)
    release_parser = sub.add_parser("hold-release")
    release_parser.add_argument("timestamp")
    sub.add_parser("hold-list")
    args = parser.parse_args(argv)

    try:
        require_root()
        config = load_config(Path(args.config))
        manager_lock = with_lock(config.lock_path) if args.command in {"create", "prune", "run", "legacy-delete", "hold-add", "hold-release", "hold-list"} else None
        writer_lock = None
        try:
            if args.command in {"create", "run"} and config.writer_lock_path is not None:
                writer_lock = with_lock(config.writer_lock_path, shared=True, require_existing=True)
            if args.command == "create":
                create_all(config, args.timestamp)
            elif args.command == "prune":
                prune(config, args.dry_run)
            elif args.command == "list":
                show_list(config)
            elif args.command == "status":
                show_status(config)
            elif args.command == "legacy-plan":
                legacy_plan(config, args.legacy_map, args.json)
            elif args.command == "legacy-delete":
                legacy_delete(config, Path(args.approval_file), args.source, args.snapper_config,
                              args.snapshot_id, args.execute)
            elif args.command in {"hold-add", "hold-release", "hold-list"}:
                checkpoint_command(config, args.command, getattr(args, "timestamp", None), getattr(args, "reason", None))
            elif args.command == "run":
                create_all(config)
                prune(config, False)
        finally:
            if writer_lock is not None:
                writer_lock.close()
            if manager_lock is not None:
                manager_lock.close()
        return 0
    except SnapshotError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

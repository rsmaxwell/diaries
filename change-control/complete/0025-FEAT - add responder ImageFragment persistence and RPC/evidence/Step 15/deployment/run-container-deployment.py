"""0025 Step 15.2/15.3 controlled responder deployment and validation.

Runs the locally built responder candidate against disposable PostgreSQL and Mosquitto
containers plus a private temporary file tree.  It never connects to the live development
DB, production DB, or NAS.  The responder itself
uses an isolated container and a dynamically allocated loopback HTTP port.
"""
from __future__ import annotations

from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import socket
import os
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
STEP15 = HERE.parent
FEATURE = STEP15.parent.parent
ROOT = FEATURE.parent.parent.parent

if len(sys.argv) != 2:
    raise SystemExit("usage: python run-deployment.py <new-evidence-directory>")
OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True, exist_ok=False)
WORK = ROOT / "diaries-responder" / "build" / ("step15-" + uuid.uuid4().hex[:10])
WORK.mkdir(parents=True, exist_ok=False)
DB = "diaries-0025-step15-" + uuid.uuid4().hex[:10]
BROKER = DB + "-mqtt"
owned: list[str] = []
process: str | None = None
NETWORK = DB + "-network"
network_owned = False
HTTP_PORT = 0
RUNTIME = None
current_label = None
handle = None
current_config_file: Path | None = None

result: dict = {
    "status": "RUNNING",
    "startedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "feature": "0025-FEAT - add responder ImageFragment persistence and RPC",
    "validation": ["15.2", "15.3"],
    "productionModified": False,
    "liveDatabaseUsed": False,
    "nasUsed": False,
    "httpPort": "dynamic loopback mapping",
}

TOKEN_RE = re.compile(r"eyJ[A-Za-z0-9_.-]+")

def redact(text: str) -> str:
    return TOKEN_RE.sub("[REDACTED TOKEN]", text)

def progress(message: str) -> None:
    print(f"[Step 15] {message}", flush=True)

def command(args, log: str | None = None, data: bytes | None = None, cwd: Path | None = None, timeout: float | None = None, env: dict | None = None) -> str:
    try:
        p = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, timeout=timeout, env=env)
        raw = p.stdout or b""
    except subprocess.TimeoutExpired as exc:
        raw = (exc.stdout or b"") + (exc.stderr or b"")
        text = raw.decode("utf-8", errors="replace")
        if log:
            (OUT / log).write_text(redact(text), encoding="utf-8")
        raise RuntimeError(f"{args[0]} timed out after {timeout}s: see {log or 'console output'}") from exc
    text = raw.decode("utf-8", errors="replace")
    if log:
        (OUT / log).write_text(redact(text), encoding="utf-8")
    if p.returncode:
        raise RuntimeError(f"{args[0]} exit {p.returncode}: see {log or 'console output'}; {text[-800:]}")
    return text.strip()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def sql(query: str) -> str:
    return command(["docker", "exec", DB, "psql", "-X", "-U", "diaries", "-d", "image_wiring_test", "-At", "-v", "ON_ERROR_STOP=1", "-c", query])

def require_port_free(port: int) -> None:
    # Do not bind the port: on Windows an exclusive existing listener can turn that
    # safety probe itself into WSAEACCES/10013.  A connect probe is sufficient to
    # detect the common case (the normal development responder is still running).
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.35)
        code = s.connect_ex(("127.0.0.1", port))
    if code == 0:
        raise RuntimeError(
            f"TCP/{port} is already accepting connections. Stop the existing local Diaries responder "
            "before this isolated deployment run; no process was stopped automatically."
        )

def verify_step14_inventory() -> None:
    inventory = FEATURE / "evidence" / "Step 14" / "source-sha256.csv"
    if not inventory.is_file():
        raise RuntimeError(f"Missing Step 14 source inventory: {inventory}")
    changed = []
    checked = 0
    with inventory.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rel = row["path"]
            expected = row["sha256"].lower()
            path = ROOT / Path(rel)
            checked += 1
            if not path.is_file():
                changed.append({"path": rel, "reason": "missing"})
            else:
                actual = sha256(path)
                if actual != expected:
                    changed.append({"path": rel, "expected": expected, "actual": actual})
    comparison = {"checkedFiles": checked, "changedFiles": changed, "matchesStep14": not changed}
    (OUT / "step14-source-comparison.json").write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    result["step14SourceComparison"] = comparison
    if changed:
        raise RuntimeError("Application source no longer matches Step 14 evidence; rerun regression verification before Step 15 deployment.")

def stop_responder() -> None:
    global process
    if process is not None:
        command(["docker", "logs", process], f"{current_label}-responder.log")
        command(["docker", "stop", process])
        process = None


def start_responder(config: dict, gate: bool, label: str, jar: Path) -> Path:
    global process, current_config_file, current_label, HTTP_PORT
    config = json.loads(json.dumps(config))
    config["imageFragmentWritesEnabled"] = gate
    configfile = WORK / f"responder-{label}.json"
    current_config_file = configfile
    current_label = label
    configfile.write_text(json.dumps(config, indent=2), encoding="utf-8")
    responder = DB + "-responder"
    command(["docker", "run", "-d", "--rm", "--name", responder, "--network", NETWORK,
             "--user", "root", "--workdir", "/fixture", "-p", "127.0.0.1::8081",
             "--mount", f"type=bind,source={WORK},target=/fixture",
             "--mount", f"type=bind,source={jar},target=/opt/candidate.jar,readonly",
             "--entrypoint", "java", RUNTIME, "-jar", "/opt/candidate.jar", "--config", "/fixture/"+configfile.name], f"{label}-container.txt")
    process = responder
    HTTP_PORT = int(command(["docker", "port", responder, "8081"]).split(":")[-1])
    result.setdefault("deployments", []).append({"phase":label,"container":responder,"httpPort":HTTP_PORT,
        "imageFragmentWritesEnabled":gate,"jarSha256":result["jarSha256"]})
    return configfile

def wait_responder_ready(label: str, jar: Path, configfile: Path) -> None:
    progress(f"{label}: waiting for responder MQTT RPC readiness")
    deadline = time.time() + 120
    attempt = 0
    attempts: list[str] = []
    health_env = os.environ.copy()
    # The disposable broker allows anonymous access, but the production health-check
    # client deliberately requires credentials.  These values exist only for this fixture.
    health_env["DIARIES_MQTT_HEALTH_USERNAME"] = "fixture-health"
    health_env["DIARIES_MQTT_HEALTH_PASSWORD"] = "fixture-health"
    while time.time() < deadline:
        attempt += 1
        if process is None:
            raise RuntimeError(f"Responder exited while waiting for {label} readiness")
        try:
            p = subprocess.run(
                ["docker", "exec", "-e", "DIARIES_MQTT_HEALTH_USERNAME=fixture-health", "-e", "DIARIES_MQTT_HEALTH_PASSWORD=fixture-health", process, "java", "-cp", "/opt/candidate.jar", "com.rsmaxwell.diaries.responder.health.ResponderHealthCheck", "--config", "/fixture/"+configfile.name],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=6, env=health_env
            )
            text = (p.stdout or b"").decode("utf-8", errors="replace")
            attempts.append(f"--- attempt {attempt}; exit={p.returncode} ---\n{redact(text)}")
            if p.returncode == 0:
                (OUT / f"{label}-health.log").write_text("\n".join(attempts), encoding="utf-8")
                progress(f"{label}: responder health RPC passed on attempt {attempt}")
                return
        except subprocess.TimeoutExpired as exc:
            text = ((exc.stdout or b"") + (exc.stderr or b"")).decode("utf-8", errors="replace")
            attempts.append(f"--- attempt {attempt}; timeout ---\n{redact(text)}")
        time.sleep(1)
    (OUT / f"{label}-health.log").write_text("\n".join(attempts), encoding="utf-8")
    raise RuntimeError(f"Responder MQTT RPC readiness timeout during {label}; see {label}-health.log and {label}-responder.log")

def phase(label: str, mqtt_port: int) -> None:
    progress(f"{label}: starting Node MQTT RPC smoke phase")
    command(
        ["node", str(HERE / "smoke.cjs"), str(ROOT), str(OUT), label, str(mqtt_port), str(HTTP_PORT), DB],
        f"{label}-console.log", timeout=180,
    )
    progress(f"{label}: Node MQTT RPC smoke phase passed")

def wait_postgres() -> None:
    deadline = time.time() + 60
    while time.time() < deadline:
        if subprocess.run(["docker", "exec", DB, "pg_isready", "-U", "diaries"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return
        time.sleep(0.25)
    raise RuntimeError("PostgreSQL readiness timeout")

def wait_broker() -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        if subprocess.run(["docker", "exec", BROKER, "mosquitto_pub", "-h", "127.0.0.1", "-t", "fixture/ready", "-m", "ready"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return
        time.sleep(0.25)
    raise RuntimeError("Mosquitto readiness timeout")

try:
    progress("checking local port and Step 14 source inventory")
    # HTTP port is dynamically mapped by Docker; existing host responders are untouched.
    verify_step14_inventory()
    progress("Step 14 source inventory matches")

    # Build the exact source just compared with Step 14.  This is a deployment build,
    # not a substitute for the already-completed Step 14 regression run.
    if os.name == "nt":
        gradle_args = ["cmd.exe", "/d", "/c", str(ROOT / "gradlew.bat"), "-p", str(ROOT), ":diaries-responder:shadowJar", "--rerun-tasks", "--console=plain"]
    else:
        gradle_args = [str(ROOT / "gradlew"), "-p", str(ROOT), ":diaries-responder:shadowJar", "--rerun-tasks", "--console=plain"]
    progress("building responder candidate JAR")
    command(gradle_args, "candidate-build.log")
    progress("responder candidate build completed")
    jars = sorted((ROOT / "diaries-responder" / "build" / "libs").glob("diaries-responder-*-fat.jar"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jars:
        raise RuntimeError("Responder fat JAR was not produced")
    jar = jars[0]
    result["jar"] = str(jar)
    result["jarSha256"] = sha256(jar)
    try:
        result["javaVersion"] = command(["java", "-version"], "java-version.txt")
    except Exception:
        raise RuntimeError("Java 25 runtime is required to run the responder candidate")
    result["nodeVersion"] = command(["node", "--version"], "node-version.txt")
    result["dockerVersion"] = command(["docker", "--version"], "docker-version.txt")

    baseline = ROOT / "change-control" / "complete" / "0024-FEAT - introduce reusable persistent Image catalogue"
    frozen_summary = json.loads((baseline / "evidence" / "phase-09-validation" / "run" / "validation-summary.json").read_text(encoding="utf-8"))
    backup = ROOT / "data" / "database-backups" / "development-infrastructure" / "diaries-development-20260912-203528.dump"
    if not backup.is_file():
        raise RuntimeError(f"Frozen development backup is missing: {backup}")
    result["backupSha256"] = sha256(backup)
    if result["backupSha256"] != frozen_summary["backupSha256"]:
        raise RuntimeError("Frozen development backup no longer matches 0024 evidence")
    result["frozenBackupMatched"] = True

    pg_image = command(["docker", "image", "inspect", "postgres:18-alpine", "--format", "{{.Id}}"], "postgres-image-id.txt")
    mqtt_image = command(["docker", "image", "inspect", "eclipse-mosquitto:2", "--format", "{{.Id}}"], "mosquitto-image-id.txt")
    RUNTIME = command(["docker", "image", "inspect", "diaries-responder:local", "--format", "{{.Id}}"], "runtime-image.txt")
    command(["docker", "network", "create", NETWORK])
    network_owned = True
    result.update(postgresImage=pg_image, mosquittoImage=mqtt_image, runtimeImage=RUNTIME, deployment="candidate JAR mounted into isolated runtime container")

    progress("starting disposable PostgreSQL and restoring frozen development backup")
    command(["docker", "run", "-d", "--rm", "--name", DB, "--network", NETWORK, "--tmpfs", "/var/lib/postgresql", "-e", "POSTGRES_USER=diaries", "-e", "POSTGRES_DB=image_wiring_test", "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-p", "127.0.0.1::5432", pg_image], "database-container.txt")
    owned.append(DB)
    wait_postgres()
    command(["docker", "cp", str(backup), f"{DB}:/tmp/baseline.dump"])
    command(["docker", "exec", DB, "pg_restore", "-U", "diaries", "-d", "image_wiring_test", "--no-owner", "--no-privileges", "/tmp/baseline.dump"], "restore.log")

    schema = baseline / "migration" / "schema.sql"
    command(["docker", "cp", str(schema), f"{DB}:/tmp/0024-schema.sql"])
    command(["docker", "exec", DB, "psql", "-X", "-U", "diaries", "-d", "image_wiring_test", "-v", "ON_ERROR_STOP=1", "-f", "/tmp/0024-schema.sql"], "0024-schema.log")
    migration = FEATURE / "migration"
    command(["docker", "cp", str(migration), f"{DB}:/tmp/migration"])
    command(["docker", "exec", DB, "psql", "-X", "-U", "diaries", "-d", "image_wiring_test", "-v", "ON_ERROR_STOP=1", "-f", "/tmp/migration/001-preflight.sql", "-f", "/tmp/migration/002-add-fragment-image-reference.sql", "-f", "/tmp/migration/003-postflight.sql"], "0025-schema.log")
    progress("frozen database restored and 0024/0025 schema verified")

    # Change only the disposable restored copy of one user so RPC authentication is deterministic.
    helper = WORK / "FixturePassword.java"
    helper.write_text('class FixturePassword { public static void main(String[] a) {System.out.print(org.mindrot.jbcrypt.BCrypt.hashpw("Step15-only",org.mindrot.jbcrypt.BCrypt.gensalt()));}}', encoding="utf-8")
    password_hash = command(["java", "-cp", str(jar), str(helper)])
    columns = sql("select column_name from information_schema.columns where table_name='person'").splitlines()
    pwcolumn = next((x for x in columns if x.lower().replace("_", "") == "passwordhash"), None)
    if not pwcolumn:
        raise RuntimeError("Could not identify person password hash column")
    sql(f'''UPDATE person SET username='step15',"{pwcolumn}"='{password_hash}',role='EDITOR',status='ACTIVE' WHERE id=(SELECT min(id) FROM person)''')

    tables = ["diary", "page", "fragment", "marquee", "image", "person"]
    snap = " UNION ALL ".join(
        f"SELECT '{t}',count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM {t} t" for t in tables
    )
    before = sql(snap)
    (OUT / "database-before.txt").write_text(before + "\n", encoding="utf-8")

    conf = WORK / "mosquitto.conf"
    conf.write_text("listener 1883\nallow_anonymous true\npersistence false\nmax_inflight_messages 20\nmax_queued_messages 10000\n", encoding="utf-8")
    progress("starting disposable Mosquitto broker")
    command(["docker", "run", "-d", "--rm", "--name", BROKER, "--network", NETWORK, "-p", "127.0.0.1::1883", "--mount", f"type=bind,source={conf},target=/mosquitto/config/mosquitto.conf,readonly", mqtt_image], "broker-container.txt")
    owned.append(BROKER)
    wait_broker()
    db_port = int(command(["docker", "port", DB, "5432"]).split(":")[-1])
    mqtt_port = int(command(["docker", "port", BROKER, "1883"]).split(":")[-1])

    config = {
        "db": {
            "host": DB, "port": 5432, "database": "image_wiring_test",
            "jdbc": {"dbms": "postgresql", "driver": "org.postgresql.Driver"},
            "admin": {"username": "diaries", "password": ""},
            "users": [{"username": "diaries", "password": ""}],
            "additionalConnectionProperties": {"hibernate.hbm2ddl.auto": "validate"},
        },
        "mqtt": {"host": BROKER, "port": 1883, "user": {"username": "fixture", "password": "fixture"}},
        "diaries": {"root": "/fixture/content", "diaries": "diaries", "files": "files"},
        "refreshPeriod": "1h", "refreshExpiration": "2h",
        "secret": "U3RlcDE1LWRpc3Bvc2FibGUtc2lnbmluZy1rZXktMDAwMQ==",
        "normaliseOnStartup": False,
        "imageFragmentWritesEnabled": False,
    }
    (OUT / "fixture-config-redacted.json").write_text(json.dumps({**config, "secret": "[DISPOSABLE SECRET REDACTED]"}, indent=2) + "\n", encoding="utf-8")

    progress("disposable PostgreSQL/Mosquitto fixtures are ready")

    # 15.2: candidate deployed with authoring disabled.  Exercise ordinary MARQUEE,
    # existing reads, upload/catalogue, unreferenced delete and DeleteFile protection.
    progress("15.2: starting candidate with ImageFragment writes disabled")
    disabled_config = start_responder(config, False, "disabled", jar)
    wait_responder_ready("disabled", jar, disabled_config)
    phase("disabled", mqtt_port)
    stop_responder()

    # 15.3: explicitly controlled IMAGE authoring, then retained corruption + restart
    # replay, reference-aware conflict and successful delete after final reference removal.
    progress("15.3: starting candidate with controlled ImageFragment writes enabled")
    enabled_config = start_responder(config, True, "enabled", jar)
    wait_responder_ready("enabled", jar, enabled_config)
    phase("enabled", mqtt_port)
    stop_responder()
    progress("15.3: corrupting retained fixture state before restart/replay")
    phase("corrupt", mqtt_port)
    replay_config = start_responder(config, True, "replay", jar)
    wait_responder_ready("replay", jar, replay_config)
    phase("replay-delete", mqtt_port)
    stop_responder()

    after = sql(snap)
    (OUT / "database-after.txt").write_text(after + "\n", encoding="utf-8")
    if before != after:
        raise RuntimeError("Original disposable database rows changed after controlled fixture cleanup")
    controlled = WORK / "content" / "files" / "step15" / "images" / "step15.png"
    if controlled.exists():
        raise RuntimeError("Controlled fixture file remains after successful deletion")
    result.update(status="PASSED", databaseRowsUnchanged=True, controlledFileAbsent=True)
    progress("controlled deployment validation passed; beginning cleanup")
except Exception as exc:
    progress(f"validation failed: {exc}")
    result.update(status="FAILED", error=str(exc))
finally:
    stop_responder()
    result["cleanup"] = {}
    if BROKER in owned:
        try:
            broker_log = subprocess.run(["docker", "logs", BROKER], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10).stdout.decode("utf-8", errors="replace")
            (OUT / "mosquitto.log").write_text(redact(broker_log), encoding="utf-8")
        except Exception as log_error:
            result["brokerLogCaptureError"] = str(log_error)
    for item in reversed(owned):
        p = subprocess.run(["docker", "stop", item], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result["cleanup"][item] = p.returncode
        if p.returncode and result.get("status") == "PASSED":
            result["status"] = "CLEANUP_FAILED"
    if network_owned:
        p = subprocess.run(["docker", "network", "rm", NETWORK], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result["cleanup"][NETWORK] = p.returncode
        if p.returncode: result["status"] = "CLEANUP_FAILED"
    for log in OUT.glob("*.log"):
        text = log.read_text(encoding="utf-8", errors="replace")
        log.write_text(redact(text), encoding="utf-8")
    try:
        if not WORK.resolve().is_relative_to((ROOT / "diaries-responder/build").resolve()):
            raise RuntimeError("Refusing cleanup outside responder build directory")
        shutil.rmtree(WORK)
        result["workDirectoryRemoved"] = True
    except Exception as cleanup_error:
        result["workDirectoryRemoved"] = False
        result["workDirectoryCleanupError"] = str(cleanup_error)
        if result.get("status") == "PASSED":
            result["status"] = "CLEANUP_FAILED"
    result["finishedAtUtc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if result.get("status") != "PASSED":
    raise SystemExit(1)

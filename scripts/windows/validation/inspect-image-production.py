"""Read-only 0024 production assessment; run via Python stdin on the target host.

Requires Docker access. Does not write files, execute migrations, alter services,
read password files or include configuration secrets in its JSON output.
"""
import datetime
import hashlib
import json
import pathlib
import socket
import subprocess
import unicodedata


def command(arguments):
    result = subprocess.run(arguments, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def sql(query):
    return command([
        "docker", "exec", "diaries-postgres", "sh", "-c",
        'exec psql -XAt -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
        '-v ON_ERROR_STOP=1 -c "$1"', "sh",
        "BEGIN READ ONLY; " + query + "; ROLLBACK;",
    ]).splitlines()[1:-1]


responder = json.loads(command(["docker", "inspect", "diaries-responder"]))[0]
config = json.loads(command([
    "docker", "exec", "diaries-responder", "cat", "/config/responder.json"
]))
files = str(pathlib.PurePosixPath(config["diaries"]["root"]) / config["diaries"]["files"])
report = {
    "host": socket.gethostname(),
    "capturedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mode": "READ_ONLY",
    "configuration": {
        "filesRoot": files,
        "normaliseOnStartup": config.get("normaliseOnStartup"),
        "database": {key: config["db"].get(key) for key in ("host", "port", "database")},
    },
    "components": [],
}
for name in ("diaries-responder", "diaries-client", "diaries-web", "diaries-postgres", "diaries-mosquitto"):
    probe = subprocess.run(["docker", "inspect", name], text=True, capture_output=True)
    if probe.returncode:
        report["components"].append({"name": name, "present": False})
        continue
    data = json.loads(probe.stdout)[0]
    report["components"].append({
        "name": name, "present": True, "image": data["Config"]["Image"],
        "imageId": data["Image"], "status": data["State"]["Status"],
        "health": data["State"].get("Health", {}).get("Status"),
        "workingDirectory": data["Config"].get("Labels", {}).get("com.docker.compose.project.working_dir"),
    })
report["mounts"] = []
for mount in responder["HostConfig"].get("Mounts", []):
    item = {key: mount.get(key) for key in ("Type", "Source", "Target", "ReadOnly", "VolumeOptions")}
    if mount.get("Type") == "volume":
        volume = json.loads(command(["docker", "volume", "inspect", mount["Source"]]))[0]
        # Never serialize volume option 'o': it contains NAS credentials.
        item["device"] = volume.get("Options", {}).get("device")
        item["filesystem"] = volume.get("Options", {}).get("type")
    report["mounts"].append(item)
report["schema"] = json.loads(sql("""
    SELECT json_build_object('database',current_database(),'version',version(),
      'imageTable',to_regclass('public.image'),
      'unicodeCollation',to_regcollation('pg_catalog.pg_unicode_fast'))
""")[0])
report["chronology"] = []
for table in ("diary", "page", "fragment", "marquee"):
    report["chronology"].append(json.loads(sql(
        "SELECT json_build_object('table','" + table + "','count',count(*),"
        "'rowHash',md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]'))) FROM " + table + " t"
    )[0]))
if report["schema"]["imageTable"]:
    report["imageRows"] = int(sql("SELECT count(*) FROM public.image")[0])
else:
    report["imageRows"] = None
digest_lines = command([
    "docker", "exec", "diaries-responder", "find", files,
    "-type", "f", "-exec", "sha256sum", "{}", ";",
]).splitlines()
report["files"] = []
for line in digest_lines:
    digest, filename = line.split("  ", 1)
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("Unexpected sha256sum output; inspect unsupported filenames separately")
    relative = str(pathlib.PurePosixPath(filename).relative_to(files))
    report["files"].append({"relativePath": relative, "sha256": digest})
report["files"].sort(key=lambda entry: entry["relativePath"])
report["fileCount"] = len(report["files"])
report["inventorySha256"] = hashlib.sha256(json.dumps(report["files"], sort_keys=True).encode()).hexdigest()
aliases = {}
for entry in report["files"]:
    aliases.setdefault(unicodedata.normalize("NFC", entry["relativePath"]).casefold(), []).append(entry["relativePath"])
report["caseFoldedAliases"] = [values for values in aliases.values() if len(values) > 1]
report["filesystemType"] = command(["docker", "exec", "diaries-responder", "stat", "-f", "-c", "%T", files])
report["rootPermissions"] = command(["docker", "exec", "diaries-responder", "stat", "-c", "%a %u:%g", files])
staging = subprocess.run([
    "docker", "exec", "diaries-responder", "stat", "-c", "%a %u:%g", files + "/.image-staging"
], text=True, capture_output=True)
report["stagingPermissions"] = staging.stdout.strip() if staging.returncode == 0 else None
print(json.dumps(report, indent=2))

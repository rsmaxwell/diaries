# Feature: Remove MQTT credentials from the Diaries Git repository

## Background

The Diaries application currently stores MQTT credential material in the Git repository under:

`config/mosquitto`

In particular, the repository currently contains:

- `config/mosquitto/pwfile.source.txt`
- `config/mosquitto/pwfile.txt`

`pwfile.source.txt` contains plaintext MQTT usernames and passwords.

`pwfile.txt` is the generated Mosquitto password file containing hashed passwords.

Neither file should be stored in Git.

The existing MQTT users are:

- `admin`
- `diaries-client`
- `diaries-responder`
- `diaries-health`

The existing Mosquitto ACL in:

`config/mosquitto/aclfile.txt`

defines application permissions for:

- `diaries-client`
- `diaries-responder`
- `diaries-health`

These usernames and the existing ACL behaviour must be preserved.

---

# Objective

Change MQTT credential handling so that:

1. plaintext MQTT passwords are never stored in the Diaries Git repository;
2. the generated Mosquitto `pwfile.txt` is also treated as generated credential material and is not stored in Git;
3. all three local development modes obtain the plaintext credential source from:

   `%USERPROFILE%\.diaries\pwfile.source.txt`

   which is equivalent to:

   `$HOME/.diaries/pwfile.source.txt`

4. local development continues to generate:

   `config/mosquitto/pwfile.txt`

   using the existing Mosquitto password-generation mechanism;

5. production generates its Mosquitto password file from the existing Ansible MQTT username/password variables stored in:

   `/etc/ansible/host_vars/<host>`

   with MQTT passwords protected using Ansible Vault;

6. the existing MQTT usernames, authentication behaviour, ACL behaviour and health check continue to work;

7. no plaintext MQTT passwords are written into generated change-control documentation, proposed source files, logs or normal Ansible output.

---

# Existing local implementation

The current local password-generation mechanism is:

`config/mosquitto/mosquitto-passwd.bat`

This currently:

1. changes to `config/mosquitto`;
2. copies:

   `pwfile.source.txt`

   to:

   `pwfile.txt`;

3. starts:

   `eclipse-mosquitto:2`

4. mounts `config/mosquitto` as `/work`;
5. invokes:

   `/work/generate-pwfile.sh`

The existing:

`config/mosquitto/generate-pwfile.sh`

then:

1. copies `/work/pwfile.txt` to a temporary file;
2. applies restrictive permissions;
3. runs:

   `mosquitto_passwd -U`

   against the temporary file;

4. copies the hashed result back to:

   `/work/pwfile.txt`;

5. sets the resulting file owner and permissions.

Preserve this mechanism unless a small change is required to support the new source-file location.

Do not introduce a second, competing local password-generation mechanism.

---

# Local-development requirements

The three supported local execution modes are:

- `development-infrastructure`
- `local-docker-build`
- `local-published-smoke`

Their Compose files are:

- `compose.development-infrastructure.yaml`
- `compose.local-docker-build.yaml`
- `compose.local-published-smoke.yaml`

All three currently mount:

`./config/mosquitto/pwfile.txt`

as:

`/mosquitto/config/pwfile.txt`

read-only inside the `diaries-mqtt` container.

That runtime arrangement should remain unchanged unless there is a compelling reason to alter it.

The change is primarily concerned with how `config/mosquitto/pwfile.txt` is produced.

## Local source file

Replace the current source:

`config/mosquitto/pwfile.source.txt`

with the external developer-specific source:

`%USERPROFILE%\.diaries\pwfile.source.txt`

Do not copy the external plaintext source permanently into the repository.

The file must retain the format expected by `mosquitto_passwd -U`:

`username:password`

and must contain entries for the existing MQTT identities:

- `admin`
- `diaries-client`
- `diaries-responder`
- `diaries-health`

Do not put example real passwords into the repository.

## Update `mosquitto-passwd.bat`

Update:

`config/mosquitto/mosquitto-passwd.bat`

so that its input is:

`%USERPROFILE%\.diaries\pwfile.source.txt`

instead of:

`config/mosquitto/pwfile.source.txt`

It should continue to produce:

`config/mosquitto/pwfile.txt`

and should continue to use the existing:

`config/mosquitto/generate-pwfile.sh`

and:

`eclipse-mosquitto:2`

mechanism to execute `mosquitto_passwd -U`.

The script must check that:

`%USERPROFILE%\.diaries\pwfile.source.txt`

exists before doing anything else.

If it does not exist, terminate with a non-zero exit code and a clear message similar to:

`MQTT password source file not found: %USERPROFILE%\.diaries\pwfile.source.txt`

There must be no fallback to the old repository copy.

The script must not display the contents of the source file.

## Generated `pwfile.txt`

Continue to generate:

`config/mosquitto/pwfile.txt`

because all three Compose modes already mount that path into Mosquitto.

However, `pwfile.txt` must become an ignored generated file rather than a Git-controlled file.

Ensure that:

- `config/mosquitto/pwfile.txt` is removed from Git;
- an appropriate `.gitignore` rule prevents it from being accidentally committed again;
- the generated file remains available locally after running `mosquitto-passwd.bat`.

The Compose files should not require changes simply to accommodate this feature if they can continue mounting the generated file from the existing location.

---

# Local MQTT health check

The three local Compose configurations provide these environment variables to the `diaries-mqtt` container:

- `DIARIES_MQTT_HEALTH_USERNAME`
- `DIARIES_MQTT_HEALTH_PASSWORD`

The health check uses:

`mosquitto_sub`

to connect to localhost and subscribe once to:

`$SYS/broker/version`

The intended health-check identity is:

`diaries-health`

The ACL already gives:

`diaries-health`

read access to:

`$SYS/broker/version`

Preserve this mechanism.

Do not solve this feature by reverting the health check to the `admin` MQTT account.

The password supplied through `DIARIES_MQTT_HEALTH_PASSWORD` must match the password represented by the `diaries-health` entry in the external local:

`%USERPROFILE%\.diaries\pwfile.source.txt`

Existing local environment/local.env conventions should continue to be used for supplying the health-check environment variables.

Do not introduce plaintext MQTT passwords into committed `.env` files.

---

# Application MQTT identities

Preserve the existing MQTT identities and their roles.

## Client

Username:

`diaries-client`

The ACL permits this identity to perform the MQTT operations required by the Diaries client.

## Responder

Username:

`diaries-responder`

The responder configuration already uses this username.

The ACL permits this identity to read requests, write responses and read/write the application data topics required by the responder.

## Health check

Username:

`diaries-health`

The ACL permits this identity to read:

`$SYS/broker/version`

The Mosquitto Docker health check authenticates with this identity using:

- `DIARIES_MQTT_HEALTH_USERNAME`
- `DIARIES_MQTT_HEALTH_PASSWORD`

## Administrator

Username:

`admin`

Retain the existing administrative MQTT account.

Do not unnecessarily change the existing ACL or MQTT account model as part of this feature.

---

# Existing production implementation

The production Ansible role currently performs password generation in:

`roles/diaries/tasks/pwfile.yaml`

The current implementation:

1. calculates a SHA-256 checksum of a controller-side:

   `misc/config/mosquitto/pwfile.source.txt`;

2. checks the installed:

   `{{ diaries_project_dir }}/config/mosquitto/pwfile.txt`;

3. checks:

   `{{ diaries_project_dir }}/config/mosquitto/pwfile.source.sha256`;

4. decides whether the password file needs regenerating;

5. creates a temporary plaintext file on the target;

6. copies the controller-side plaintext `pwfile.source.txt` into it;

7. runs:

   `mosquitto_passwd -U`

   against the temporary file;

8. installs the hashed result as:

   `{{ diaries_project_dir }}/config/mosquitto/pwfile.txt`;

9. installs a checksum marker;

10. deletes the temporary file.

The resulting Mosquitto password file currently has:

- owner `1883`;
- group `1883`;
- mode `0600`.

Preserve these runtime ownership and permission characteristics unless inspection of the current Mosquitto container proves that a different setting is required.

---

# Existing production MQTT variables

The existing host-variable convention already provides the necessary MQTT variables.

Use these variables rather than introducing a new parallel naming scheme:

`mosquitto_admin_user`

`mosquitto_admin_password`

`mosquitto_client_user`

`mosquitto_client_password`

`mosquitto_responder_user`

`mosquitto_responder_password`

`mosquitto_health_username`

`mosquitto_health_password`

The corresponding usernames are currently:

- `mosquitto_admin_user` → `admin`
- `mosquitto_client_user` → `diaries-client`
- `mosquitto_responder_user` → `diaries-responder`
- `mosquitto_health_username` → `diaries-health`

Retain these names, including the existing `mosquitto_health_username` naming convention, rather than performing an unrelated variable-renaming exercise.

All four MQTT password variables must be treated as secrets and must be Ansible Vault encrypted in:

`/etc/ansible/host_vars/<host>`

Specifically:

- `mosquitto_admin_password`
- `mosquitto_client_password`
- `mosquitto_responder_password`
- `mosquitto_health_password`

Do not include actual password values in the Diaries source repository.

---

# Required production change

Remove the production dependency on:

`misc/config/mosquitto/pwfile.source.txt`

The production Ansible role must construct the temporary Mosquitto plaintext password source from the existing Ansible variables instead.

Conceptually, the temporary data must contain:

`{{ mosquitto_admin_user }}:<admin password>`

`{{ mosquitto_client_user }}:<client password>`

`{{ mosquitto_responder_user }}:<responder password>`

`{{ mosquitto_health_username }}:<health password>`

where the corresponding password values come from the Vault-protected variables listed above.

Do not place the literal secret values into a committed Jinja template or other repository file.

A suitable implementation is for Ansible to create the temporary plaintext file directly using `ansible.builtin.copy` with dynamically generated `content`, protected with:

`no_log: true`

and restrictive permissions.

Then continue to use:

`mosquitto_passwd -U`

to convert that temporary plaintext file into the Mosquitto hashed password file.

The temporary plaintext file must always be deleted after generation.

Do not leave a plaintext `pwfile.source.txt` anywhere under:

`{{ diaries_project_dir }}`

on the target.

---

# Production idempotence

Preserve the intention of the existing checksum-based regeneration mechanism.

Currently:

`roles/diaries/tasks/pwfile.yaml`

uses:

`{{ diaries_project_dir }}/config/mosquitto/pwfile.source.sha256`

to determine whether the generated password file is current.

Because the controller-side plaintext source file will no longer exist, change the checksum calculation so that it is derived deterministically from the username/password variable values from which the Mosquitto password file is generated.

The checksum or fingerprint must change if any relevant MQTT username or password changes.

The actual plaintext credentials must not be written to the checksum marker or Ansible logs.

The resulting behaviour should remain:

- first run: generate `pwfile.txt`;
- unchanged credentials: no regeneration;
- changed username/password: regenerate `pwfile.txt`;
- missing `pwfile.txt`: regenerate it;
- missing checksum marker: regenerate it.

The Ansible role must remain idempotent after the first successful deployment.

Tasks manipulating plaintext password data or decrypted Vault values must use `no_log: true` where appropriate.

---

# Production Compose configuration

The production Compose template currently supplies:

`DIARIES_MQTT_HEALTH_USERNAME`

from:

`mosquitto_health_username`

and:

`DIARIES_MQTT_HEALTH_PASSWORD`

from:

`mosquitto_health_password`

The `diaries-mqtt` service mounts:

`./config/mosquitto/pwfile.txt`

as:

`/mosquitto/config/pwfile.txt`

read-only.

Preserve this arrangement.

The purpose of this feature is to change how the deployed `pwfile.txt` is generated, not to redesign Mosquitto's runtime configuration.

---

# Repository cleanup

Remove the tracked files containing credential material:

`config/mosquitto/pwfile.source.txt`

`config/mosquitto/pwfile.txt`

Also remove the production/playbook plaintext source:

`misc/config/mosquitto/pwfile.source.txt`

if that file is part of the current playbooks source tree.

Update `.gitignore` as necessary so that generated:

`config/mosquitto/pwfile.txt`

cannot accidentally be recommitted.

Search the complete Diaries source tree and playbooks for references to:

- `pwfile.source.txt`
- `pwfile.txt`
- `mosquitto_passwd`
- `mosquitto_admin_password`
- `mosquitto_client_password`
- `mosquitto_responder_password`
- `mosquitto_health_password`

and update only those references necessary for this feature.

Do not perform unrelated credential refactoring.

---

# Security requirements

The completed implementation must ensure that:

- no plaintext MQTT password exists in the Git repository;
- no generated Mosquitto password database is stored in Git;
- local plaintext MQTT credentials exist only in:

  `%USERPROFILE%\.diaries\pwfile.source.txt`

  or temporary processing files;

- production plaintext MQTT credentials originate from Vault-encrypted Ansible variables;
- temporary production plaintext files are removed;
- generated production `pwfile.txt` has restrictive permissions;
- Ansible does not display decrypted MQTT passwords;
- scripts do not echo MQTT passwords;
- generated change-control documentation never contains actual passwords;
- generated `changed-files` content never contains actual passwords.

Do not copy current real passwords into documentation, test fixtures, examples or source files.

Use clearly artificial placeholders where examples are required.

---

# Migration considerations

The change must include instructions for the developer to create:

`%USERPROFILE%\.diaries\pwfile.source.txt`

before the repository-held source file is removed.

The migration instructions must document the required four usernames but must not embed the actual passwords.

Similarly, production migration instructions must explain that the following variables need valid Vault-protected values for every target host:

- `mosquitto_admin_password`
- `mosquitto_client_password`
- `mosquitto_responder_password`
- `mosquitto_health_password`

Do not automatically invent or change existing passwords as part of this feature.

---

# Change-control decomposition

Do not implement this as one large change.

Before changing the actual Diaries application, inspect the current:

`diaries/change-control`

directory and determine the next available feature numbers and existing naming convention.

Split the overall work into a sequence of small change-control features.

A likely decomposition is:

1. externalise the local MQTT plaintext credential source;
2. stop tracking generated MQTT password files;
3. change production password generation to use Ansible Vault variables;
4. remove obsolete repository/controller plaintext credential sources and complete verification/documentation.

This is guidance rather than a mandatory decomposition.

Choose the final feature boundaries after inspecting the source tree.

Each feature must:

- have one clear purpose;
- be limited in scope;
- leave the Diaries application in a working state;
- preserve compatibility with the following features;
- include suitable tests or verification;
- avoid unrelated refactoring.

When the complete sequence is implemented, all requirements in this specification must be satisfied.

---

# Development artefacts

For each proposed change-control feature create:

`diaries/change-control/todo/<feature>/DEVELOPMENT-STEPS.md`

Each `DEVELOPMENT-STEPS.md` must describe:

- purpose;
- current behaviour;
- required behaviour;
- implementation steps;
- files to add/change/delete;
- migration/setup requirements;
- tests and verification;
- expected state after completion.

Also write the complete proposed contents of every added or changed source file beneath:

`diaries/change-control/todo/<feature>/changed-files`

Preserve the real repository-relative path beneath `changed-files`.

For example, a proposed change to:

`config/mosquitto/mosquitto-passwd.bat`

would be stored beneath:

`changed-files/config/mosquitto/mosquitto-passwd.bat`

Clearly identify files that are to be deleted rather than silently omitting them.

Never put real passwords, decrypted Ansible Vault values or other credentials into either `DEVELOPMENT-STEPS.md` or `changed-files`.

---

# Tests and verification

The proposed change-control sequence must include verification of at least the following.

## Local

For each of:

- `development-infrastructure`
- `local-docker-build`
- `local-published-smoke`

verify that:

1. `$HOME/.diaries/pwfile.source.txt` exists;
2. `config/mosquitto/pwfile.txt` can be generated successfully;
3. Mosquitto starts;
4. the Mosquitto health check becomes healthy;
5. `diaries-health` can read `$SYS/broker/version`;
6. `diaries-responder` can connect;
7. client/responder MQTT communication works;
8. removing `$HOME/.diaries/pwfile.source.txt` causes password generation to fail with a useful error;
9. neither plaintext nor generated password files are tracked by Git.

## Production

Verify that:

1. the playbook succeeds without `misc/config/mosquitto/pwfile.source.txt`;
2. `pwfile.txt` is generated from the Ansible variables;
3. no plaintext password source remains on the target;
4. `pwfile.txt` has the expected ownership and mode;
5. Mosquitto starts and becomes healthy;
6. the responder connects successfully;
7. an unchanged second Ansible run does not regenerate the password file;
8. changing an MQTT credential causes regeneration;
9. normal Ansible output contains no MQTT password values.

---

# Important implementation boundary

This request is initially an analysis and change-preparation task only.

Do not modify the actual Diaries application source tree or production playbooks in-place.

First create only the proposed change-control artefacts under:

`diaries/change-control/todo/<feature>`

including:

- `DEVELOPMENT-STEPS.md`
- `changed-files`

After preparing all proposed features, provide a summary containing:

1. the feature numbers and names;
2. the purpose of each feature;
3. the order in which they should be implemented;
4. all files that would be added, changed or deleted;
5. local migration requirements;
6. production migration requirements;
7. security-sensitive points;
8. assumptions made;
9. any remaining risks or unresolved decisions.

Then stop.

Ask me whether I want the complete set of prepared features implemented in the actual Diaries and playbooks source trees.

Do not implement the actual changes until I explicitly approve that next step.
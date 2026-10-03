# Step 15 documentation requirement matrix

| Step 15 requirement | Normal documentation location(s) |
| --- | --- |
| One effective database dataset ↔ one mutable Files root | `README.md`, `ARCHITECTURE.md`, `scripts/windows/README.md`, `roles/diaries/README.md` |
| `local.env` is loaded second and overrides mode defaults | `README.md`, `ARCHITECTURE.md`, `scripts/windows/README.md`, `local.env.example` |
| Normal local common database may be `./data/database/common` | same local docs plus `diaries-responder/README.md` |
| Common database override must use `files-development-common` | same local docs and `local.env.example` |
| Shared read-only `diaries` versus mutable Files | `README.md`, `ARCHITECTURE.md`, `scripts/windows/README.md`, Playbooks docs |
| `DIARIES_FILES_DIR` leaf-directory semantics | `README.md`, `ARCHITECTURE.md`, `diaries-responder/README.md`, `scripts/windows/README.md`, `local.env.example` |
| Production `diaries_files_dir` | `ARCHITECTURE.md`, `roles/diaries/README.md`, production scripts README |
| Direct Windows generated responder configuration | `README.md`, `diaries-responder/README.md`, `scripts/windows/README.md` |
| Restore isolated committed defaults | `README.md`, `ARCHITECTURE.md`, `scripts/windows/README.md`, `local.env.example` |
| `/files/...` and `Image.relativePath` stay environment-neutral | `README.md`, `ARCHITECTURE.md`, responder/Windows/Playbooks docs |
| Complete dataset backup | top-level README/architecture plus Windows and Playbooks operating docs |
| Restore a matched database + Files pair | same backup/restore operating docs |
| Identify effective Files root before destructive tests | `README.md`, `scripts/windows/README.md`, production scripts README |
| One-sided database/Files switching is invalid | all local pairing docs plus Playbooks role/scripts docs |
| Danger of re-sharing independently changed datasets | top-level README/architecture plus Windows and Playbooks operating docs |

The matrix deliberately points to normal operating documentation. Future operators do not need this 0031 evidence directory to learn the rule; this file only records that Step 15 covered each requested subject.

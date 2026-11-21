# 0051 Step 4 — production evidence register

**Prepared:** 21 November 2026. **Purpose:** navigation/traceability, not a replay of private evidence. All paths below are relative to the 0051 feature root unless otherwise shown.

| Event | Grounded result | Original evidence reference |
| --- | --- | --- |
| Published-image protected rehearsal | PASS, `20261120T210259Z-de695753`; runner asserts rollback before first extension write, re-upgrade, forward-only activation | `evidence/Step 4/private/published-20261120T210259Z-de695753/`; user terminal log `note(20261120-210437).txt`; existing `STEP4-PUBLISHED-REHEARSAL-REVIEW-20261120.md` |
| Harness correction history | Separate earlier failing receipts retained, followed by successful Docker Linux Files volume fix | Existing Step 4 correction reports; `note(20261120-205843).txt`, `note(20261120-210437).txt` |
| Production baseline + recovery | Original images 84/77/8; manifest backup `20261120-003112Z` healthy on mars and backup | `note(20261120-210725).txt`, `note(20261120-211158).txt`, `note(20261120-211317).txt`, `note(20261120-211347).txt` |
| Deployment with extension gate off | Ansible 55 OK/3 changed/0 failed; schema 4096 nullable; 5 healthy | `note(20261120-212610).txt`, `note(20261120-212836).txt` |
| Responder logs | No WARN/ERROR in bounded subsequent query; earlier broad grep falsely matched diary word “exceptionally” | `note(20261120-213719).txt` |
| Day Reader rendering defect, fix and regressions | Corrective Angular regression 244/244; local production build passed; four-file client commit `7e0251d`; parent `aace22f` | `note(20261120-215723).txt`, `note(20261121-072702).txt`, `note(20261121-073132).txt`, `note(20261121-073211).txt` |
| Jenkins client build-79 | SUCCESS; digest `sha256:d0202347952543b34db301a74a413068c15f765763d0d402f00f742f94e60f93` | `note(20261121-073553).txt` |
| Client 79 local acceptance + NAS mount correction | All 5 healthy, no Docker volume mismatch; owner screenshot displayed local IMAGE 2338/Image ID 3 | `note(20261121-075110).txt`, 21 Nov IMAGE screenshot in chat |
| Client 79 production redeploy + health | `pluto ok=55 changed=3 failed=0`, client 79/responder 85/web 9, PostgreSQL and Mosquitto healthy; extension gate off | `note(20261121-082045).txt`, `note(20261121-082142).txt`; owner production Fragment 2332 visual confirmation |
| Extension gate activation | 21 Nov 09:03Z, current manifest reports HEALTHY; Ansible 55 OK/2 changed/0 failed, five healthy, both write gates on | `evidence/Step 4/production-activation-20261121T090357Z.log` **on Windows**, corresponding uploaded `note(20261121-090630).txt` |
| Final production behaviour | Owner: “0051 production activation functional checks all passed” | 21 Nov Diaries project owner message; **no independently inspected per-action browser/DB receipt supplied in this exchange** |

## Current release identities

- Diaries parent `aace22faa2f2bf64f146b33dfc8714e43005cf1d` pins client `7e0251d1c47720397504f3fd43fff09b6b7f2bb3`; responder `0aa08bd2851c9615f65aabd329b8858399742d27`; web `f6142567d856d4c1110be93673497938276190d5`.
- Production image tags after final activation: client `0.0.9-build-79`, responder `0.0.9-build-85`, reader `0.0.9-build-9`.
- Playbooks last observed on `mango`: `main`, revision `c13b1d5c690c879a4464b0a302aefda92d6335f8` **with uncommitted 0051 changes**; the effective applied state is corroborated by deployed configuration and health checks, not a claimed committed Playbooks revision. Recheck the working tree before any eventual commit.

## Evidence handling

The original logs, private 0028 review material, screenshots, dump/restore data, release manifests and backup records remain in their respective existing feature evidence directories or terminal uploads. **Do not copy private raw transcriptions, credentials, review decisions or production database exports into a new public ZIP.**

A final acceptance receipt can reference this register and the checked-in files. Verify local path existence and Git status on Windows during Step 5; if a source receipt is missing, note it rather than inventing its content or hash.

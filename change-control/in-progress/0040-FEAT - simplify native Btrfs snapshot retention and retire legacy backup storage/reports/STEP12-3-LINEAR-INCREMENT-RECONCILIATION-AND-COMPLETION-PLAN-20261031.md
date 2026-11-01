# 0040-FEAT Step 12.3 — Linear increment reconciliation and completion plan

Date: 2026-10-31  |  Status: PROPOSED PLAN; STEP OPEN  |  Execution mode: staged, fail-closed

## Authority and purpose

Governing document: `STEP-12-3-UNATTENDED-DESIGN-DECISION.md` — **Unattended receiver-pruning redesign**. Six implementation gates are defined there and remain the formal closure conditions. The October 30 `reports/STEP12-3-AGREED-PARENT-REDESIGN-20261030.md` introduces a **durable agreed-parent** protocol as the safety foundation for independent sender/receiver pruning; it does not replace the six closure gates.

Objective: safe, recoverable, unattended native Btrfs replication and independent local retention pruning, preserving the latest verified common parent, any in-flight parent, historic holds and receiver receipts/journals, without per-delete operator approval.

## Naming decision

- Step remains **0040-FEAT Step 12.3**. Its increments are **linear, not hierarchical**.
- Preserve filenames and raw logs labelled `04A` through `04U` for traceability. They are 21 consecutive *lettered* integrations in the recent series, **not** substeps of a future Increment 05. Do not rename earlier documents or invent a mapping for earlier `3G`, `3H`, Stage B, etc.
- Future execution work shall use the next agreed **linear numeric increment** after reconciling the full existing Step 12.3 index; no further `04V`, `04W` labels. Use descriptive titles (e.g. `Step 12.3 — Receiver authenticated handoff`) and only assign a numeric increment after checking the historical index for collisions. The proposed next number `22` is provisional, not an assertion that all earlier 12.3 labels are sequential.
- Small test contracts are supporting evidence, **not** independent formal acceptance gates.

## Evidence inventory (as of 2026-10-31 conversation)

| Area | Evidence reported | What this proves / does not prove |
|---|---|---|
| Durable A/B | Live A established at both ends, B pending at both ends | Prepared state, not received B or completed transition |
| 04A–04G | Review and import-only transfer contract tests | No binary Btrfs transfer; older 04F SSH invocation identity needs remediation |
| 04H | Receiver destination absence and authenticated source-to-receiver check passed | Absence at observation time, not absence guaranteed through receive |
| 04I–04J | Boundary contract regressions; 04J deployed and live locked review passed | Locks/preflight review; no receive callback in production |
| 04K–04O | Receipt/completion/framing/session source regressions passed | Protocol validation only; no authenticated integrated transport or durable receipt commit |
| 04P | Both real SSH probes from mars to backup authenticated as `richard` | Independent SSH identities, **not** session binding |
| 04Q–04R | Receiver session binding/coordinator simulated regressions passed | No trusted live SSH registrations |
| 04S | Review coordinator installed on backup; live A/B lock-scoped session review `rc=0` | Real manager/writer locks and absence; zero registered channels, no transfer |
| 04T–04U | Local kernel `SO_PEERCRED` and restricted socket regressions passed | Local process identity only; no proof of originating SSH session, no install |

Recent console logs above are conversation evidence until copied into the feature's permanent `evidence/Step 12/` or `reports/` area. Source ZIP snapshots (Diaries 08:50 and Playbooks 08:50) predate some accepted 04P–04U local changes; validate current `mango` working tree before implementing.

## Shortest safe completion sequence (not yet accepted)

**Gate A — Freeze and reconcile (read-only).** Verify Git branch/revision/status, role names, installed artifacts, lock paths, SSH execution identity, active systemd timers and current A/B on both hosts. Reconcile all recent ZIP changes not present in the 08:50 source bundles. Retain historical evidence. No snapshot modification.

**Gate B — Choose one integrated receiver architecture.** Decide whether to reuse the existing authenticated single-SSH pipeline with a trusted completion mechanism, or to implement the two-channel registration design. Do not add a privileged socket endpoint merely to satisfy the existing contracts. For a two-channel design, specify precisely how SSH authentication is asserted by a trusted server-side boundary, how `SO_PEERCRED` maps to it, how both connections reach one lock-owning process, directory ownership/permissions, deadlines and binary framing. Produce an executable sequence diagram and failure matrix, then review before code. Do not grant new broad sudo privileges (0041-FEAT handles privilege separation).

**Gate C — Integrate a single bounded A→B receive.** Revalidate A/B and destination absence under manager and writer locks; hold both through binary receive, independent B identity and read-only/parent verification, authenticated sender completion and durable receipt commit. Use the real `richard` SSH identity. Treat any ambiguous exit or incomplete artifact as failed, preserving A and B evidence without automatic retry/deletion. Ensure the legacy entrypoint cannot bypass the same safety protocol. First prove on disposable Btrfs.

**Gate D — Verify durable parent advance and recovery.** Exercise A→B and B→C, each commit/ack interruption and reconciliation, disagreeing endpoint records, duplicate registrations/receipts and concurrent prune/receive. Do not retire A until durable convergence on both ends. Reuse earlier accepted correctness evidence where it directly covers a gate; avoid redundant full restores.

**Gate E — Restore independent unattended pruning.** Implement/share one prune algorithm on both ends via configuration, enforcing local pins, holds, receipts, retention 48 hourly / 14 daily / 12 weekly / 24 monthly / 5 yearly, 30-minute minimum age and journal recovery. Run source tests and disposable real-Btrfs receive/prune/concurrency/stale-qgroup scenarios. No source/receiver interactive per-delete approval.

**Gate F — Controlled deployment and closure.** Ansible `--check --diff`, reviewed deploy host-by-host, live read-only observations, intentional schedule enablement only with approval, idempotency and unattended-cycle evidence; verify rollback. Inspect legacy approval directories before retirement. Archive logs and acceptance against the six original design gates. Mark Step 12.3 CLOSED **only after formal acceptance of all six gates**. Move 0040-FEAT to `complete` only on feature-level closure.

## Immediate next action

Do **Gate A** as a strictly read-only baseline. Verify the real, current `mango` Playbooks checkout and compare installed review modules before deciding any more code. Then produce the **Gate B architectural decision** using existing code and tests, avoiding another chain of dormant validators.

## Safety hold

- Keep native push and snapshot prune stopped on `mars`; allow hourly snapshot creation to continue.
- Do not delete snapshots, receipts, historical holds or journals, or initiate Btrfs send/receive.
- Current last accepted state: A `20261030-030033Z` / UUID `d901ddd2-66c7-0b42-b26c-ab6886273b7a`; B `20261030-170009Z` / UUID `a9b78fb9-4da6-cf4f-b242-13909f574193`; `previous=null` on both hosts. These are **last observed**, not an assertion of current live state.
- All gates remain OPEN unless independently evidenced and formally accepted; this report is a plan, not production authorisation.

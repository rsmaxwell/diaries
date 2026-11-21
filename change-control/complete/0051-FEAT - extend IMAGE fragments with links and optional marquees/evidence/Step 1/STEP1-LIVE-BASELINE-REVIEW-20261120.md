# 0051 Step 1 — Live production baseline review (20 November 2026)

**Status:** live read-only inspection PASS; Windows Cygwin static test FAIL due solely to a Python annotation compatibility error; Step 1 acceptance **OPEN**. This is a review of the terminal output provided by the owner, not an independent live execution. Raw output is retained locally in ignored `evidence/Step 1/private/live-production-baseline.log` and is deliberately not included in the change package.

## Windows checkout at inspection

The parent contains previously present uncommitted 0028/0029 documentation edits and an untracked 0051 feature directory. Preserve these edits. Reported submodule revisions:

| Component | Revision |
|---|---|
| diaries-client | `89c9d539d79bd6b235ab28aa55ea600c86aa4fce` |
| diaries-responder | `bd65d08435c0f5d240337cd6479cb41befe4d8c1` |
| diaries-web | `cc147426e93ee6952558b65147e444d38316b3ce` |

These are checkout state, not deployment commit IDs.

## Live inspection, captured at 2026-11-20 10:47:37 UTC

| Component | Running image | Status |
|---|---|---|
| responder | `rsmaxwell/diaries-responder:0.0.9-build-84` | running; healthy |
| client | `rsmaxwell/diaries-client:0.0.9-build-77` | running; healthy |
| web reader | `rsmaxwell/diaries-web:0.0.9-build-8` | running; healthy |
| database | `postgres:18-alpine` | running; healthy |
| broker | `eclipse-mosquitto:2` | running; healthy |

Responder configuration: `imageFragmentWritesEnabled=true` (existing IMAGE authoring, **not** authorisation for new link/Marquee combinations).

### PostgreSQL schema findings

- `fragment` has nullable `type VARCHAR(16)`, nullable `image_id BIGINT`, and nullable `page_id BIGINT`; **no `image_link_url` column** at inspection time.
- `fragment_type_check`: non-null `type` must be `MARQUEE` or `IMAGE`; legacy null type remains allowed.
- `fragment_image_type_check`: a non-null `image_id` requires a non-null `IMAGE` type. `fragment_image_fk` references `image(id)`; `fragment_image_id_idx` exists.
- `marquee.fragment_id BIGINT NOT NULL` has a foreign key to `fragment(id)` and a **UNIQUE** constraint; hence at most one Marquee row per Fragment. `marquee.page_id BIGINT` is nullable and has a separate foreign key to `page(id)`.
- **No database constraint enforcing `marquee.page_id = fragment.page_id`** appears in the supplied schema output. Same-Page enforcement must be verified/implemented in responder logic, including existing inconsistent/legacy associations.
- All schema queries used a read-only inspection transaction that visibly ended in `ROLLBACK`. No write or deployment was performed by this script.

These observations support the Step 1 proposed additive URL migration; they do **not** establish that current responder and reader code can handle IMAGE+Marquee.

## Local static test failure and remedy

The Windows Cygwin invocation of `tests/step1-static-baseline.py` failed before executing any of its twelve source checks:

```text
TypeError: 'type' object is not subscriptable
```

The cause is the function annotation `list[str]` (and, on Python before 3.10, `list[str] | None`). The test was originally run successfully in a newer Python environment, not in the owner's Cygwin interpreter. Replace the annotations with `typing.List[str]` and `typing.Optional[List[str]]`, compatible with older Python 3 versions. This changes no test assertions, operational scripts or application code.

**Required local follow-up:** rerun the static baseline in Cygwin and retain its actual output under `evidence/Step 1/private/`; do not report a Cygwin pass until that output is reviewed. No reason to repeat live production inspection purely to repair a local test.

## Outstanding Step 1 acceptance items

1. Confirm the compatibility-fixed static baseline completes in the Windows Cygwin checkout.
2. Review/accept the proposed cross-component URL, RPC set/clear/preserve and IMAGE Marquee/same-Page contract and the comprehensive regression matrix.
3. Run representative **synthetic application runtime** baseline checks in an isolated supported DB/MQTT/Files mode; static source checks and live schema inspection do not substitute for this.
4. Recheck checkout and submodule status before modifying code. Do not alter production, resume 0028 or mark Step 1 CLOSED on this evidence alone.

## Subsequent verification (20 November 2026)

The compatibility-fixed Cygwin static source baseline subsequently passed 12/12 checks
under Python 3.7.12. All three selected local application runtime test groups also
passed; see [runtime baseline review](STEP1-RUNTIME-BASELINE-REVIEW-20261120.md).
The earlier failure and originally outstanding items above are preserved as a
chronological record rather than silently replaced. Step 1 owner acceptance remains OPEN.

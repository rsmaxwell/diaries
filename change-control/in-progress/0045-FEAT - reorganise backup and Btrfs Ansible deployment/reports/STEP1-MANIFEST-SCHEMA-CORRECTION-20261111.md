# 0045 Step 1 — Capture wrapper schema correction (11 November 2026)

## Observation

The definitive Step 1 capture at 20261111-111426Z completed Windows source/inventory capture and reached the `mars` static-manifest step, then exited without a collector diagnostic. Five focused `dpkg-query` parser tests had already passed.

## Root cause

The version-2 host collector produces `schema=0045-static-installed-v2`, while the surrounding `capture-0045-step1-baseline.sh` still checked for a literal `0045-static-installed-v1`. The host collector could succeed but the wrapper's silent `grep -Fq` check then failed. This is a contract mismatch in the capture tooling, not evidence of a host installation failure.

## Correction

The wrapper now validates the generated JSON by parsing it and checking `schema=0045-static-installed-v2`, expected hostname, all seven static sections and a nonempty managed-files section. Capture failures report whether host execution, manifest validation, or health readback failed. The correction is read-only and does not modify `mars`, `backup` or their timers/services.

## Verification before distribution

- `bash -n` syntax: PASS
- Simulated v2 manifest: PASS
- Simulated obsolete v1 manifest: refused, with diagnostic
- Simulated missing section: refused, with diagnostic
- Simulated host mismatch: refused, with diagnostic

The preceding incomplete capture remains historical diagnostic evidence. Step 1 is not closed until a new definitive capture succeeds on both hosts and its coverage is reviewed.

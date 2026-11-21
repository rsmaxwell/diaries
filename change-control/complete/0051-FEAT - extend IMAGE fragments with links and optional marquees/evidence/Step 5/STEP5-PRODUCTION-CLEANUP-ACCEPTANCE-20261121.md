# 0051-FEAT — Final production cleanup acceptance

Date: 21 November 2026

## Implementation

The following development options were permanently retired:

- imageFragmentWritesEnabled
- imageFragmentExtensionsWritesEnabled

IMAGE authoring, external links and optional Marquees are now
normal functionality for authorised Editors.

Authentication, locking, version checks and validation remain.

## Verification

| Check | Result |
|---|---|
| Responder Java regression tests | PASS |
| Local Docker integration | PASS |
| Local IMAGE GUI tests (5/5) | PASS — owner confirmed |
| Jenkins responder build-86 | SUCCESS |
| Production Ansible deployment | PASS |
| Production container health (5/5) | PASS |
| Obsolete configuration properties absent | PASS |
| Production IMAGE browser check | PASS — owner confirmed |
| Playbooks deployment contract | PASS |
| Playbooks Git integration | PASS |

## Production versions

- Client: 0.0.9-build-79
- Responder: 0.0.9-build-86
- Web: 0.0.9-build-9

## Git revisions

- Diaries parent implementation: 94d2b91ac06a7fba9594e2c2b41edcfe10dccc30
- Diaries responder: 4109c37eb64ea8f8f513a439628d75145f658634
- Playbooks: 417de0887109324b5f78ba0fc1bd5591625e4f12
- Ansible controller: 8efacfa26acaddbea2e0dd2eeab7c8947b29462a

## Production deployment evidence

- production-gate-cleanup-20261121T115921Z.log
- Previously accepted Step 4 and Step 5 evidence

## Handoff

- 0028 legacy embedded-image migration remains separate.
- 0029 IMAGE lifecycle work remains separate.
- 0052 Whitley Park map defect remains TODO.

## Closure

Implementation, deployment and functional acceptance are complete.

Formal 0051-FEAT closure remains subject to owner approval.

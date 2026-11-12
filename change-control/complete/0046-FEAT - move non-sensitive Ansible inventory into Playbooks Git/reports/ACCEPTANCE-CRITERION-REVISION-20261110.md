# 0046-FEAT — Acceptance-criterion clarification (10 November 2026)

**Status:** planning amendment only; no implementation or deployment.

## Accepted interpretation

The binding result for 0046 is **installation equivalence across the entire managed estate**: for **every managed host and applicable playbook**, the installation produced with the relocated Playbooks Git inventory must match the installation produced with the original `/etc/ansible` inventory, using the **same frozen post-0045 installation-producing Playbooks revision** and other relevant inputs.

The earlier draft made exact effective-variable values and precedence independent closure gates and reserved full installed-state equality for `mars` and `backup`. Those restrictions are **superseded**. Variable values/precedence remain important debugging information, and preserving them is often the simplest implementation, but they need not be identical when no installed-result, target-selection, credential or security difference results. `mars`/`backup` remain in scope but **do not delimit** the verification estate.

## Acceptance impact

- Step 1 captures an inventory of **all managed hosts, relevant playbooks and installed baseline footprints**, not just the Btrfs machines.
- Step 2 may use a securely designed Vault loader with different precedence if installation and security behaviour stay identical.
- Step 3 requires a complete **host-by-playbook installation-equivalence matrix** supported by repeatable installed-state manifests and safe deterministic/control-run evidence; syntax, `--list-hosts`, variable-map matches and representative-host tests cannot by themselves close the feature.
- Step 4 closure requires accepted zero-installation-difference results for **every managed host and applicable playbook**. A host that cannot be verified keeps the feature OPEN until addressed or its scope is formally amended.

No source, inventory, Vault or target-host change has been performed by this documentation update. **0046 remains PLANNED**, dependent on formal completion of 0045.

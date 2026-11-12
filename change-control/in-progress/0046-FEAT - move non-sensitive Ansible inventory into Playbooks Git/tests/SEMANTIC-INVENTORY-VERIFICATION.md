# 0046 protected inventory semantic verification

`tools/verify-0046-prepared-inventory.py --self-test` verifies that expected Ansible Vault JSON wrappers can be normalised, and that unrelated changes or malformed wrappers fail the comparison. The same verifier checks the live prepared inventory read-only.

The script must report 44 matching paths, 12 expected altered files, 14 exact YAML scalar decryption matches, eight expected active JSON Vault wrappers, and zero other inventory differences. A pass does not authorise a Git push until private repository visibility and the staged-content checks are accepted.

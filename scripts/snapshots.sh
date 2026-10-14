#!/bin/bash
set -euo pipefail

cd ~/playbooks

host="${1:-mars}"
ansible-playbook --limit "${host}" snapshots.yaml

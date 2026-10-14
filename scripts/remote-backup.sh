#!/bin/bash
set -euo pipefail

cd ~/playbooks

ansible backup -m ping 1>/dev/null 2>/dev/null
ansible-playbook remote-backup.yaml

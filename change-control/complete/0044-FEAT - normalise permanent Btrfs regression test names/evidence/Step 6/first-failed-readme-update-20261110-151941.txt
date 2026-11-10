richard@mango:~/playbooks$ if (
  cd /home/richard/playbooks || exit 1

  echo '=== Verify repository baseline ==='
  test "$(git branch --show-current)" = main || exit 1
  test "$(git rev-parse HEAD)" = \
    '4c17fac7455d8fa8a3f4caa1dd003eaac2427c32' || exit 1

  echo '=== Update README references ==='
  sed -i \
    -e 's/verify-simplified-replication\.py/verify-replication.py/g' \
    -e 's/verify-simplified-protection\.py/verify-protection.py/g' \
    roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md \
    roles/snapshots/tests/README-0040-SIMPLIFIED-RECEIVER-RETENTION.md \
    || exit 1

  echo '=== Check for obsolete filename references ==='
  if git grep -n -E \
    'verify-simplified-(replication|protection)\.py'; then
    echo 'FAIL: Obsolete filename references remain'
    exit 1
  fi

  echo '=== Run permanent regression suite ==='
  sudo -n env PYTHONDONTWRITEBYTECODE=1 python3 \
    roles/btrfs-replication/tests/verify-replication.py || exit 1

  sudo -n env PYTHONDONTWRITEBYTECODE=1 python3 \
fiecho 'FAIL: 0044 permanent test naming'complete'ression names' \N.md \
=== Verify repository baseline ===
=== Update README references ===
sed: can't read roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md: No such file or directory
FAIL: 0044 permanent test naming
richard@mango:~/playbooks$

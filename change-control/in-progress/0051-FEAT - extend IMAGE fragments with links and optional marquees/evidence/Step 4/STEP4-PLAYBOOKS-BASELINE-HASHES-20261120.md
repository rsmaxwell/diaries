# Step 4 Playbooks source comparison

The original hashes describe **only** the supplied 18 November Playbooks export.
They do not establish the current version on `mango`. Check the live Git status
and use Beyond Compare before applying the separate Playbooks ZIP. **Do not
deploy or enable the extension gate merely by applying this source package.**

| Playbooks repository-relative file | 18 Nov SHA-256 | Proposed SHA-256 |
|---|---|---|
| `roles/diaries/defaults/main.yaml` | `e3338179e3041e14e0460386bfc9de85d137c1a97a361c44c1d8967edbaf4fa3` | `72d8d0928e1c1d4dabe5e73367e04b3a2dec95ce82641b9b958680f99ae71829` |
| `roles/diaries/tasks/main.yaml` | `d5199c6f180d063b4cb9a3b588454897283c8ac06b0e33d37cbbee28a84eaf43` | `40085e6c9ca0cc65c0629d119e63a3e226a351563ac8701481e47c0649f4237d` |
| `roles/diaries/tasks/copy.yaml` | `5f0147e17ac3b1f88d7b11d5dc2ad0e18d5b6099a44d7bd8a92b261fc33a2bad` | `fe432ae3cc9ee0ccfc7eb4106fb90119b9d90567e72620a7c20f7a687162a57a` |
| `roles/diaries/templates/config/responder/responder.json.j2` | `678bfd57dcae1946c9544a2a0faba8846323696c3dfc56f45ad12c98f05719f3` | `66ca17776591fb4d15b42467304c56627d3b8c6d407c87ae12b1217c11364895` |

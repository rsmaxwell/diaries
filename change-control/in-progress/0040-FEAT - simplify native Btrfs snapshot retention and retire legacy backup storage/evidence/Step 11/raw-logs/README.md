# Step 11 — Raw execution evidence index (26 October 2026)

These files reproduce operator-supplied terminal transcripts. They are historical evidence, not production scripts. The SHA-256 values below attest to the bytes archived in this package.

| File | SHA-256 |
|---|---|
| `note(20261026-090048).txt` | `bf3aee4ca2d31135f0a7b4856fb0c942e071a97eb3466ced1b7488d3fcce27c4` |
| `note(20261026-114719).txt` | `9406797723b1e4a558d13a6be307f17162f7e8c9d1e16b2b8c6a46d82cd55afd` |
| `note(20261026-114957).txt` | `11946c500cf6acac01d41749b0f4b91d1d215ef721180aa26f77937c687499b4` |
| `note(20261026-115249).txt` | `043dcf965155dce566d3396229bbb2b2d55354ee6b50eb645aae859b5377e17d` |
| `note(20261026-115518).txt` | `630445c4dbe25f3dc26890ae2860c14761a3ca3213436cfcb301a22436ff0d22` |
| `note(20261026-120901).txt` | `d87eb4f0b89d2ac3e87e9fe6ff73b1b0c093927bbd5c947edf9071e101fdd677` |
| `note(20261026-121425).txt` | `dfff072666cff63e9de31e8448f894e8d6d0c07e43961569f3ab4d92262e4abb` |
| `note(20261026-123320).txt` | `791cf7f1539160b9fb1ede6c2dbf380bb5dcd7fb93fbc1428a02afbc748794b8` |
| `note(20261026-131255).txt` | `28b7c11ae54a4d23cfe41968b7177052c260a59c5ce7502e2e5992d724d09d6c` |
| `note(20261026-131430).txt` | `7d99f6440774cb7152fcd8dd2ae4d023cf293ccc1dd0d71dcf066a3577c3d139` |
| `note(20261026-131537).txt` | `a179bc14e8026a5fe3960152409a295f284f5fbf2c3f966798051bd59201cdbe` |
| `note(20261026-131748).txt` | `08a73759022cfc58eaf368141921048276898da8d2a5ca56e5158941a2802a9f` |
| `note(20261026-131902).txt` | `11efe67272b297455249c76ab2ba20c418a366a40edffa8a9b214ede38979408` |
| `note(20261026-132557).txt` | `7214f82b25f4ae06d597dad4191814deb143df36d7cf338b591f1d1215a449b2` |
| `note(20261026-132655).txt` | `2177672d9091f68fd68be79f1a59ad8b0896dd22e9a784c6d1d1a8237a759677` |

Evidence highlights: 63 root snapshots deleted; receipt reconciled; receiver `CLEAN`; original native replication scheduling restored; Ansible `--check --diff` zero changes; orphaned `80snapper` removed with rollback copy, followed by `changed=0` check and healthy APT/native snapshot timers.

Permanent receipt and Step 10 retirement manifests are held separately in the same feature evidence tree; they are not duplicated in this ZIP.

**Scope:** Step 11 CLOSED on accepted evidence; 0040-FEAT Steps 12–14 remain OPEN. 0039-DEF remains in progress.

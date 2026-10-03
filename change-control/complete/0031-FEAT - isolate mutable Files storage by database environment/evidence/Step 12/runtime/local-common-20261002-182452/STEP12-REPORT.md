# 0031 Step 12 reconciliation comparison — local-common

**Status: PASS**

Step 9 baseline: `C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries\change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment\evidence\Step 9\runtime\local-common-20261002-151207`
Step 12 run: `C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries\change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment\evidence\Step 12\runtime\local-common-20261002-182452`

## Comparison

| Check | Result | Detail |
| --- | --- | --- |
| `currentDryRunComplete` | **PASS** | outcome='DRY_RUN_COMPLETE', mode='dry-run' |
| `sameDatabaseName` | **PASS** | Step 9='diaries'; Step 12='diaries' |
| `sameReconciliationCounts` | **PASS** | Step 9={"CATALOGUED_MATCH": 85, "DIRECTORY": 10, "UNSUPPORTED": 4}; Step 12={"CATALOGUED_MATCH": 85, "DIRECTORY": 10, "UNSUPPORTED": 4} |
| `sameSemanticInventory` | **PASS** | Step 9 rows=99, sha256=2fa5fbe270bff7918ad6e09a2d5ac12e842ec7720bde902bae1899ceabf73444; Step 12 rows=99, sha256=2fa5fbe270bff7918ad6e09a2d5ac12e842ec7720bde902bae1899ceabf73444 |
| `expectedFilesSelector` | **PASS** | expected='files-development-common'; current='files-development-common' |
| `expectedDatabaseSelector` | **PASS** | expected='./data/database/common'; current='./data/database/common' |
| `physicalFilesRootChanged` | **PASS** | Step 9='\\\\nas\\photo\\nancy-and-ronald-maxwell\\documents\\sea-captains-chest\\diaries-content\\files'; Step 12='\\\\nas\\photo\\nancy-and-ronald-maxwell\\documents\\sea-captains-chest\\diaries-content\\files-development-common' |
| `summaryFilesRootLeaf` | **PASS** | summary leaf='files-development-common'; selector='files-development-common' |
| `databaseIdentityExact` | **INFO** | Step 9='diaries:16385:172.18.0.3/32:5432:18.6'; Step 12='diaries:16385:172.18.0.2/32:5432:18.6'; address/port changes are informational |
| `rootKeyExact` | **PASS** | Step 9='null'; Step 12='null'; copied roots normally differ |

## Semantic fingerprints

- Step 9 inventory: `2fa5fbe270bff7918ad6e09a2d5ac12e842ec7720bde902bae1899ceabf73444`
- Step 12 inventory: `2fa5fbe270bff7918ad6e09a2d5ac12e842ec7720bde902bae1899ceabf73444`
- Step 9 counts: `{"CATALOGUED_MATCH": 85, "DIRECTORY": 10, "UNSUPPORTED": 4}`
- Step 12 counts: `{"CATALOGUED_MATCH": 85, "DIRECTORY": 10, "UNSUPPORTED": 4}`

`lastModified` is intentionally excluded from the semantic inventory fingerprint. Directory `size` is normalized because it is filesystem metadata; regular-file sizes remain compared. All other 0024 inventory columns are compared.

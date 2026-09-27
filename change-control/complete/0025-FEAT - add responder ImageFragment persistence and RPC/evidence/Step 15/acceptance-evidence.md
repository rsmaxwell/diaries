# Acceptance evidence mapping

| Acceptance group | Evidence |
| --- | --- |
| Nullable indexed FK, type constraints, repeatability and preserved existing data | Step 2 migration scenarios; Step 15 deployment 0025-schema.log; Step 15.1 actual development verification |
| Persistence/replay and immutable Page/type; invalid relationships rejected | Full Step 14 repository/aggregate/handler contracts and Step 11 database lifecycle |
| IMAGE with/without selection, shared reusable Images, lock semantics and mixed ordering | Step 11 database lifecycle/race; Step 12/13 live RPC/gate; fresh Step 14 reruns |
| MARQUEE compatibility and additive retained field | Deployed consumer probes in new Step 14; Step 15 disabled-rpc.json with real sign-in/create/edit/delete |
| Reference mutation and canonical/date retained publication | Step 15 enabled-rpc.json, state.json and replayed-retained.json |
| Referenced DeleteImage conflict and generic file protection | Step 15 disabled/enabled/replay-delete RPC logs; Step 14 DeleteCatalogueTest and DeleteImageTest |
| Shared-reference deletion does not delete reusable Image | Step 11 lifecycle/race and Step 10 FragmentLifecycleContractTest, rerun in Step 14 |
| Recoverable file/database/MQTT deletion, failure/unknown-commit handling | Step 14 ImageCatalogueDeletionTest/ImageDeletionConcurrencyTest; Step 15 successful final deletion and tombstones |
| Attach/delete serialisation and final FK backstop | Step 11 two-order PostgreSQL race, rerun in Step 14 |
| Large retained-tree synchronisation | Step 14 dedicated fresh-broker large-tree test; Step 15 actual binary restarts |
| Fail-closed authoring | Step 13 gate contracts/live test rerun in Step 14; Step 15 disabled deployment 403; read-only production config inspection |
| Builds and clean controlled deployment | Step 14 full logs/results; Step 15 deployment result.json and before/after hashes |

Source matched the refreshed 398-file inventory before and after deployment. Production rollout remains separate, including broker barrier ACL/queue capacity and 0026/0027 readiness. Deferred work: 0026 web rendering; 0027 client authoring; 0028 reviewed legacy conversion; 0029 final lifecycle/legacy-coupling cleanup.

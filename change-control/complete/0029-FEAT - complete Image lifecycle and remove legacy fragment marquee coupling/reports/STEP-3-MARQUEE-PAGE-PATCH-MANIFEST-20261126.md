# 0029 Step 3 patch from 2026-11-26 11:47 Diaries bundle

These are full source files, not a binary patch. Review with Beyond Compare; preserve later local modifications.

| File | Original SHA256 | Package SHA256 |
|---|---|---|
| `change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/reports/STEP-3-MARQUEE-PAGE-RETIREMENT-20261126.md` | `(new)` | `71548656a3c285b8` |
| `change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/step3-restore-marquee-page-id.sql` | `(new)` | `b629dcfe85f6525f` |
| `change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/step3-retire-marquee-page-id.sql` | `(new)` | `758a41e5ecdddd89` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/MarqueeDBDTO.java` | `2aa56351e4e0f162` | `978e3def8767e0da` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddFragment.java` | `2e8b159b6dadc99e` | `bad1d3a69e93e8c6` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddMarquee.java` | `e5de26c63261695e` | `2909fb6212336cad` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateMarquee.java` | `eadecf0d4c5ab148` | `74a010323b2b0861` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/migration/migration0022/Migration0022Inventory.java` | `58d3826ebcfea188` | `aab15c47acaadb88` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/migration/migration0028/MigrationStore.java` | `6ef2a7fdd8ff346b` | `8100c29b541a2c45` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Marquee.java` | `54bdb44413ea1488` | `a3c000e1f0590ce0` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/MarqueeRepositoryImpl.java` | `fb21a06b2ae69feb` | `2b0d645afd2b7a79` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java` | `9c8ea0bb0d3fef1f` | `5ce91a9d1e0a1405` |
| `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentState.java` | `0149e5d6e1011e7c` | `04d138e395052484` |
| `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/ImageWiringIntegrationTest.java` | `d313a67bce9f0348` | `6b4e2f1918543408` |
| `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/FragmentLifecycleContractTest.java` | `5c6f9c6622a529b1` | `397c170c7e527d77` |
| `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/model/MarqueeOwnerContractTest.java` | `(new)` | `e3f9aca7fbd442f0` |
| `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/DiaryContextTest.java` | `c7ce599beb08034d` | `50b9dcca102a1d76` |
| `diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentStateTest.java` | `4cfc8f1504d59c4a` | `8a3e8fe954e68fb2` |

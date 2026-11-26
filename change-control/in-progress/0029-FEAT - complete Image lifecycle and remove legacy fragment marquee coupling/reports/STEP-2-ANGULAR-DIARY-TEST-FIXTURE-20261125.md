# Step 2 — Angular Diary component test fixture correction (25 November 2026)

## Evidence

The first integrated ChromeHeadless run executed 258 tests: 255 passed and 3 failed. All three failures occurred in `DiaryComponent` tests with `NullInjectorError: No provider for _HttpClient`, through the real `MqttService -> ConfigService` chain. The annual editor was newly rendered inside `DiaryComponent`, so its dependency injection needs to be isolated in page-navigation fixture tests.

## Correction

Provide test-only doubles for `MqttService`, `LiveObjectListService` and `FragmentLockService`. The MQTT double returns a resolved connection; the retained-list double returns an empty observable; the lock double has no network effects. Preserve the existing `RpcService` spy and all three page-navigation/resequencing assertions. No production code changed.

## Verification status

Source fixture checked against `diaries-sources-20261125-171359.zip`; ZIP integrity verified. Angular/Karma execution has not been performed by the package author. Run the ChromeHeadless suite on the Windows checkout and retain its full output under the 0029 feature evidence directory. Do not infer full end-to-end success from unit tests alone.

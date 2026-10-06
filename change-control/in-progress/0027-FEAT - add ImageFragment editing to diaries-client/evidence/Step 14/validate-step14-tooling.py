#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

step = Path(__file__).resolve().parent
project = step.parents[4]
errors = []
required = [
    'README.md','RUNBOOK.md','CHECKLIST.md','MANUAL-EVIDENCE.md',
    'tooling/step14-common.ps1','tooling/step14-begin.ps1','tooling/step14-preflight.ps1',
    'tooling/step14-run-regression.ps1','tooling/step14-rollout-rehearsal.ps1','tooling/step14-finalize.ps1',
    'tooling/check-step14-test-reports.py'
]
for rel in required:
    if not (step / rel).is_file(): errors.append(f'missing {rel}')

run = (step / 'tooling/step14-run-regression.ps1').read_text(encoding='utf-8')
for needle in [
    "test-image-catalogue.ps1", "verify-imagefragment-reader.ps1", "check-step14-test-reports.py",
    "compose.local-docker-build.yaml", "compose.local-published-smoke.yaml",
    "config','--quiet", "source-files.sha256"
]:
    if needle not in run: errors.append(f'regression runner missing contract: {needle}')

integrated = (project / 'scripts/windows/validation/test-image-catalogue.ps1').read_text(encoding='utf-8')
for needle in [
    'image-catalogue-test-mosquitto.conf', 'DIARIES_IMAGE_REPOSITORY_TEST_URL',
    'DIARIES_IMAGE_WIRING_TEST_URL', 'DIARIES_IMAGE_MQTT_TEST_URL',
    'DIARIES_BROWSER_TEST_CLIENT', 'DIARIES_BROWSER_TEST_EVIDENCE', 'DIARIES_BROWSER_TEST_MQTT',
    ':diaries-responder:test', ':diaries-responder:build', ':diaries-web:test', ':diaries-web:build',
    'npm.cmd', 'ChromeHeadless', "'run','build','--','--configuration','production'"
]:
    if needle not in integrated: errors.append(f'integrated regression runner missing contract: {needle}')
if 'change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/evidence/' in integrated:
    errors.append('permanent integrated regression still depends on removed completed-feature evidence')
broker_fixture = project / 'scripts/windows/validation/image-catalogue-test-mosquitto.conf'
if not broker_fixture.is_file():
    errors.append('permanent Image/MQTT regression broker fixture is missing')
else:
    broker_text = broker_fixture.read_text(encoding='utf-8')
    for needle in ['listener 1883', 'listener 9001', 'protocol websockets', 'allow_anonymous true', 'max_queued_messages 0']:
        if needle not in broker_text: errors.append(f'permanent broker fixture missing contract: {needle}')

rehearsal = (step / 'tooling/step14-rollout-rehearsal.ps1').read_text(encoding='utf-8')
for needle in [
    'imageFragmentWritesEnabled', 'false', 'diaries_web_files_path',
    'config --quiet', 'pull', 'up --detach --remove-orphans --wait',
    'Activating Diaries routes in shared Nginx', 'Deactivating Diaries routes in shared Nginx',
    'STOP: Step 14 does not change the gate'
]:
    if needle not in rehearsal: errors.append(f'rollout rehearsal missing contract: {needle}')

checker = (step / 'tooling/check-step14-test-reports.py').read_text(encoding='utf-8')
for needle in [
    'ImageFragmentGateConfigTest','AddFragmentContractTest','legacyRequestStillCreatesMarqueeAndReturnsFragmentWithAdditiveImageId','AddImageFragmentTest','UpdateFragmentImageTest',
    'ImageWiringIntegrationTest','liveImageFragmentRpcAndRestartReplay','filesDialogDeletionEndToEnd','registeredAddImageFragmentCommitsAndPublishes',
    'addingMiddleImageFragmentNormalisesAndPublishesSurvivingChronology',
    'addingMiddleMarqueeFragmentNormalisesAndPublishesSurvivingChronology',
    'deletingMiddleImageFragmentNormalisesAndPublishesSurvivingChronology',
    'referenceConflictIs409WithRestoredFileAndRetainedMetadata',
    'imageCatalogueDoesNotChangeVisibleChronologyAcrossReaderRestarts',
    'retainedReplayLiveImageChangesAndFreshReconnectReachHttpWithoutStaleState',
    'buildsCatalogueUrlFromPublicBaseConfiguredFilesRouteAndRelativePath'
]:
    if needle not in checker: errors.append(f'report checker missing required test: {needle}')

finalizer = (step / 'tooling/step14-finalize.ps1').read_text(encoding='utf-8')
for needle in ['regression-summary.json','test-report-check.json','reader-cross-component\\evidence\\summary.json','rollout-rehearsal.txt','Step 13 source record is not yet marked complete/closed','step14-final-summary.json']:
    if needle not in finalizer: errors.append(f'finalizer missing closure condition: {needle}')

# Permanent live scripts must remain untouched by this feature-specific harness.
live_scripts = project / 'scripts'
if any('step14' in p.name.lower() for p in live_scripts.rglob('*') if p.is_file()):
    errors.append('Step 14 feature tooling leaked into permanent scripts/')

# Reader verifier and required source tests must still exist in the candidate source.
source_requirements = [
    'scripts/windows/validation/verify-imagefragment-reader.ps1',
    'diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/FragmentLifecycleContractTest.java',
    'diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/DeleteImageTest.java',
    'diaries-web/src/test/java/com/rsmaxwell/diaries/web/mqtt/MqttProjectionIntegrationTest.java',
    'diaries-web/src/test/java/com/rsmaxwell/diaries/web/rendering/RenderingSafetyTest.java',
]
for rel in source_requirements:
    if not (project / rel).is_file(): errors.append(f'candidate source prerequisite missing: {rel}')

result = {'status': 'PASS' if not errors else 'FAIL', 'errors': errors}
print(json.dumps(result, indent=2))
if errors:
    sys.exit(1)

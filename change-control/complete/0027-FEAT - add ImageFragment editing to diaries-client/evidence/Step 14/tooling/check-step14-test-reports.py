#!/usr/bin/env python3
"""Assert that Step 14's required responder/web JUnit contracts actually ran."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

REQUIRED = {
    "diaries-responder": {
        "com.rsmaxwell.diaries.responder.config.ImageFragmentGateConfigTest": None,
        "com.rsmaxwell.diaries.responder.handlers.AddFragmentContractTest": {
            "legacyRequestStillCreatesMarqueeAndReturnsFragmentWithAdditiveImageId",
        },
        "com.rsmaxwell.diaries.responder.handlers.AddImageFragmentTest": None,
        "com.rsmaxwell.diaries.responder.handlers.UpdateFragmentImageTest": None,
        "com.rsmaxwell.diaries.responder.handlers.FragmentLifecycleContractTest": {
            "addingMiddleImageFragmentNormalisesAndPublishesSurvivingChronology",
            "addingMiddleMarqueeFragmentNormalisesAndPublishesSurvivingChronology",
            "deletingMiddleImageFragmentNormalisesAndPublishesSurvivingChronology",
            "deletingOneSharedReferenceLeavesOtherFragmentAndImageUntouched",
            "updateRejectsCrossTypeMutationsBeforeAnyWriteOrPublication",
        },
        "com.rsmaxwell.diaries.responder.handlers.DeleteImageTest": {
            "referenceConflictIs409WithRestoredFileAndRetainedMetadata",
        },
        "com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest": {
            "liveImageFragmentRpcAndRestartReplay",
            "imageFragmentDatabaseLifecycleWithRealRetainedTopics",
            "mixedFragmentLifecyclePreservesReusableImage",
            "filesDialogDeletionEndToEnd",
            "registeredAddImageFragmentCommitsAndPublishes",
            "freshContextReplaysCommittedImageFragmentContract",
            "databaseReplayAddsUnreferencedImagesAndPreservesChronologyTopics",
            "registeredDeleteImageRemovesRowFileAndRetainedTopic",
        },
    },
    "diaries-web": {
        "com.rsmaxwell.diaries.web.projection.ProjectionServiceTest": {
            "sharedImageUpdatesAndTombstonesRepairEveryImageReferenceWithoutChangingChronology",
            "mixedTypesPreserveDateSequenceAndIdOrdering",
        },
        "com.rsmaxwell.diaries.web.rendering.RenderingSafetyTest": {
            "buildsCatalogueUrlFromPublicBaseConfiguredFilesRouteAndRelativePath",
            "browserVisibleCatalogueUrlsUseOnlyThePublicBaseAndEncodeLiteralRouteData",
        },
        "com.rsmaxwell.diaries.web.mqtt.MqttProjectionIntegrationTest": {
            "imageCatalogueDoesNotChangeVisibleChronologyAcrossReaderRestarts",
        },
        "com.rsmaxwell.diaries.web.mqtt.Step12MqttHttpIntegrationTest": {
            "retainedReplayLiveImageChangesAndFreshReconnectReachHttpWithoutStaleState",
        },
        "com.rsmaxwell.diaries.web.http.WebServerTest": {
            "mixedTypedFragmentsRemainAvailableThroughMonthAndSourceHttpResponses",
        },
    },
}

def read_component(root: Path, component: str):
    report_dir = root / component / "build/test-results/test"
    if not report_dir.is_dir():
        raise RuntimeError(f"Missing JUnit report directory: {report_dir}")
    cases: dict[str, dict[str, dict[str, bool]]] = {}
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for report in sorted(report_dir.glob("TEST-*.xml")):
        tree = ET.parse(report)
        suite = tree.getroot()
        for key in totals:
            totals[key] += int(suite.attrib.get(key, "0"))
        for case in suite.findall("testcase"):
            cls = case.attrib.get("classname", "")
            reported_name = case.attrib.get("name", "")
            # Gradle's JUnit XML uses JUnit 5 display names for testcase names,
            # e.g. methodName() or methodName(Path), while the Step 14 contract
            # inventory deliberately records stable Java method names only.
            # Compare on the method-name portion so harmless display signatures
            # do not make an executed test look missing.
            name = reported_name.split("(", 1)[0]
            cases.setdefault(cls, {})[name] = {
                "failure": case.find("failure") is not None,
                "error": case.find("error") is not None,
                "skipped": case.find("skipped") is not None,
                "reportedName": reported_name,
            }
    return totals, cases

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    result = {"status": "PASSED", "components": {}, "required": []}
    failures: list[str] = []
    for component, required_classes in REQUIRED.items():
        try:
            totals, cases = read_component(root, component)
        except Exception as exc:
            failures.append(str(exc)); continue
        result["components"][component] = totals
        if totals["tests"] <= 0 or totals["failures"] or totals["errors"] or totals["skipped"]:
            failures.append(f"{component}: totals are not clean: {totals}")
        for cls, methods in required_classes.items():
            available = cases.get(cls)
            if available is None:
                failures.append(f"{component}: required class did not execute: {cls}")
                continue
            names = set(available)
            targets = sorted(names if methods is None else methods)
            if methods is not None:
                missing = sorted(methods - names)
                for name in missing:
                    failures.append(f"{component}: required test did not execute: {cls}.{name}")
            for name in targets:
                state = available.get(name)
                if state is None:
                    continue
                item = {"component": component, "class": cls, "test": name, **state}
                result["required"].append(item)
                if state["failure"] or state["error"] or state["skipped"]:
                    failures.append(f"{component}: required test not clean: {cls}.{name}: {state}")
    if failures:
        result["status"] = "FAILED"
        result["failures"] = failures
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Step 14 required JUnit contracts all executed cleanly.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

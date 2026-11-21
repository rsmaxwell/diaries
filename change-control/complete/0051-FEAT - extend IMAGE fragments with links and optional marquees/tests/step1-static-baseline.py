#!/usr/bin/env python3
"""0051 Step 1: read-only static pre-change behaviour baseline.

This checks actual supplied source text. It does not execute a Java/Angular/web
runtime, connect to a database/broker, or certify 0051 feature behaviour.
Run it from the Diaries repository root or from anywhere else.
"""
from pathlib import Path
from typing import List, Optional
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PASS = 0
FAIL = 0


def check(label: str, path: str, required: List[str], forbidden: Optional[List[str]] = None) -> None:
    global PASS, FAIL
    file_path = ROOT / path
    try:
        source = file_path.read_text(encoding="utf-8")
        misses = [text for text in required if text not in source]
        present = [text for text in (forbidden or []) if text in source]
        if misses or present:
            print(f"FAIL {label} — missing={misses!r}, unexpectedly_present={present!r}")
            FAIL += 1
        else:
            print(f"PASS {label}")
            PASS += 1
    except OSError as exc:
        print(f"FAIL {label} — {exc}")
        FAIL += 1


check('existing writer rejects IMAGE+Marquee',
      'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentState.java',
      ['IMAGE fragment cannot have a Marquee'])
check('existing fragment update rejects IMAGE+Marquee',
      'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragment.java',
      ['IMAGE Fragment cannot have a Marquee', 'args.containsKey("imageId")', 'requireLockedByCaller'])
check('existing AddMarquee forces MARQUEE type',
      'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddMarquee.java',
      ['fragment.setType(FragmentType.MARQUEE)', 'FragmentLocking.requireMarqueeCompatible'])
check('existing DeleteFragment rejects IMAGE+Marquee',
      'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteFragment.java',
      ['Remove the invalid Marquee with deleteMarquee'])
check('current reader IMAGE branch ignores linked marquee',
      'diaries-web/src/main/java/com/rsmaxwell/diaries/web/projection/ProjectionSnapshot.java',
      ['An IMAGE never exposes a selected Marquee'])
check('current reader rendering gates hasMarquee by type',
      'diaries-web/src/main/java/com/rsmaxwell/diaries/web/http/WebServer.java',
      ['effectiveType == FragmentType.MARQUEE && resolved.marquee().isPresent()'])
check('current Day reader Image label after Position',
      'diaries-client/src/app/dayview/dayview.component.html',
      ['Position {{fragment.sequence}}', 'imageReferenceLabel(fragment)'])
check('current Day reader Image text',
      'diaries-client/src/app/dayview/dayview.component.ts',
      ['? `Image ${fragment.imageId}`', "'No Image selected'"])
check('current client IMAGE guard excludes Marquee',
      'diaries-client/src/app/model/fragment.ts',
      ["type: 'IMAGE'; marqueeId: null", "fragment.type === 'IMAGE' && fragment.marqueeId === null"])
check('current RPC null adapter limited to Image reference',
      'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageFragmentMessageHandler.java',
      ['request.args().containsKey("imageId")', 'request.args().get("imageId") != null'])
check('native Fragment DTO mapping has no URL',
      'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImpl.java',
      ['list.add("image_id")', 'Long imageId = getLongFromSqlResult(result, 9, null)'],
      ['image_link_url'])
check('old web retained model has no URL',
      'diaries-web/src/main/java/com/rsmaxwell/diaries/web/model/FragmentItem.java',
      ['@JsonProperty("imageId") Long imageId'],
      ['imageLinkUrl'])
print(f'RESULT: {PASS} source-baseline checks PASS, {FAIL} FAIL; read-only / no application runtime executed')
sys.exit(0 if FAIL == 0 else 1)

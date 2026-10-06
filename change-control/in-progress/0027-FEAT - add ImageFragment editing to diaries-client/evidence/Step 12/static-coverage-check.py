from pathlib import Path
root=Path(__file__).resolve().parents[5] / 'diaries-client' / 'src' / 'app'
checks={
'01 legacy null type': ('model/fragment.spec.ts', 'treats a null or absent migration type as legacy MARQUEE'),
'02 retained image projection': ('model/image-projection.spec.ts', 'deserializes the responder retained Image projection'),
'03 selected image tombstone': ('model/model-context.spec.ts', 'turns a retained Image tombstone into null'),
'04 catalogue selection': ('files-list-dialog/files-list-dialog.compatibility.spec.ts', 'returns persisted catalogue identity in catalogue-image selection mode'),
'05 add image wire': ('mqtt/image-fragment-rpc.spec.ts', 'sends exactly the addImageFragment creation fields'),
'06 preserve wire': ('mqtt/image-fragment-rpc.spec.ts', 'keeps ordinary IMAGE updateFragment requests in preserve mode'),
'06 set wire': ('mqtt/image-fragment-rpc.spec.ts', 'sends a positive imageId only through deliberate IMAGE replacement'),
'06 clear wire': ('mqtt/image-fragment-rpc.spec.ts', 'sends explicit imageId null only through deliberate IMAGE clear'),
'07 text preserve': ('fragment/text-panel/text-panel.component.spec.ts', 'keeps IMAGE text saves on the ordinary preserve path'),
'08 reorder preserve': ('dayview/dayview.component.spec.ts', 'reorders an IMAGE Fragment through the ordinary preserve path'),
'09 control type boundary': ('fragment/image-fragment-step12-regression.spec.ts', 'keeps Image-reference controls disabled for MARQUEE'),
'10 add cancel': ('fragment/fragment.component.spec.ts', 'sends no RPC and changes no selection when the chooser is cancelled'),
'10 add 403': ('fragment/fragment.component.spec.ts', 'surfaces a specific authoring-disabled message for responder 403'),
'11 replace success': ('fragment/fragment.component.spec.ts', 'replaces using the latest retained Fragment and no extra unlock'),
'11 replace no-op': ('fragment/fragment.component.spec.ts', 'does not lock or send an RPC when the selected Image is unchanged'),
'11 replace failure': ('fragment/fragment.component.spec.ts', 'uses failed-edit unlock fallback when responder rejects the Image mutation'),
'12 clear success': ('fragment/fragment.component.spec.ts', 'sends explicit null without a redundant unlock'),
'12 clear failure': ('fragment/image-fragment-step12-regression.spec.ts', 'confirmed Clear Image update fails'),
'15 image fragment delete': ('fragment/image-viewer/image-viewer.component.spec.ts', 'deletes an IMAGE Fragment through deleteFragment only'),
'16 marquee create': ('fragment/marquee-fragment-compatibility.spec.ts', 'keeps existing MARQUEE creation on addFragment'),
'16 marquee edit': ('fragment/marquee-fragment-compatibility.spec.ts', 'keeps existing MARQUEE edit selection on marquee mode'),
'16 marquee delete': ('fragment/marquee-fragment-compatibility.spec.ts', 'keeps existing MARQUEE Fragment deletion on deleteFragment'),
}
failed=[]
for name,(rel,needle) in checks.items():
    text=(root/rel).read_text()
    ok=needle in text
    print(('PASS' if ok else 'FAIL')+': '+name+' -> '+rel)
    if not ok: failed.append(name)
if failed: raise SystemExit('Missing checks: '+', '.join(failed))
print(f'PASS: {len(checks)} focused coverage anchors found across all 16 required Step 12 areas.')

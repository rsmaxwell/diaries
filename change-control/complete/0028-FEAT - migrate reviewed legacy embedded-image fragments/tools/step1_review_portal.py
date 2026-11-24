#!/usr/bin/env python3
"""0028 Step 1: generate an offline, PRIVATE manual review portal and validate its drafts.

Never alters reviewed source evidence; never authorises database or MQTT writes.
Standard library only. Use with the frozen 0028 inventory and unapproved proposal CSV.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

SCHEMA = "0028-human-review-v1"
DECISIONS = ("CONVERT_TO_IMAGE", "SPLIT_MARQUEE_AND_IMAGE", "KEEP_LEGACY", "DEFER")
ACTIONS = ("REMOVE_AS_IMAGE", "KEEP_INLINE", "DEFER")
FIELDS = (
    "disposition", "occurrence_action", "approved_page_id", "page_provenance",
    "suffix_verified", "marquee_handling", "link_handling", "text_allocation",
    "review_note", "reviewed_by", "reviewed_at", "caption_override",
)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def verify_manifest(directory: Path) -> None:
    manifest = directory / 'SHA256SUMS.txt'
    if not manifest.is_file():
        raise ValueError(f'Missing SHA256SUMS.txt in {directory}')
    for line in manifest.read_text(encoding='utf-8').splitlines():
        expected, name = line.strip().split(maxsplit=1)
        name = name.removeprefix('*').strip()
        if '/' in name or "\\\\" in name or name in ('', '..'):
            raise ValueError('Invalid manifest path')
        payload = (directory / name).read_bytes()
        if digest(payload) != expected:
            raise ValueError(f'HASH MISMATCH: {name}')


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


class SingleCaptionExtractor(HTMLParser):
    """Capture one unambiguous original figcaption as plain text, never execute HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.caption_count = 0
        self.depth = 0
        self.text_parts = []
        self.interactive = False

    def handle_starttag(self, tag, attrs):
        if tag == 'figcaption':
            self.caption_count += 1
            self.depth += 1
        elif self.depth and tag in ('a', 'script', 'style', 'iframe', 'object'):
            self.interactive = True

    def handle_endtag(self, tag):
        if tag == 'figcaption' and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.text_parts.append(data)

    def result(self):
        caption = ' '.join(' '.join(self.text_parts).split())
        if self.caption_count == 0:
            return '', 'NONE'
        if self.caption_count != 1 or self.depth or self.interactive or not caption:
            return '', 'REQUIRES_MANUAL_REVIEW'
        return caption, 'UNIQUE_FIGCAPTION'


def extract_caption(original_html: str) -> tuple[str, str]:
    parser = SingleCaptionExtractor()
    parser.feed(original_html)
    parser.close()
    return parser.result()


def resolve_caption(row: dict, caption_override: str = '') -> tuple[str, str]:
    """An explicit override wins; blank means verified single original figcaption."""
    override = (caption_override or '').strip()
    if override:
        return override, 'REVIEWER_OVERRIDE'
    if row.get('verified_caption_status') == 'UNIQUE_FIGCAPTION':
        return row.get('verified_original_caption', ''), 'EXISTING_FIGCAPTION'
    # Used only by old/synthetic checker tests; real input is verified above.
    if 'verified_caption_status' not in row and row.get('proposal_caption_plaintext_PRIVATE'):
        return row['proposal_caption_plaintext_PRIVATE'], 'EXISTING_FIGCAPTION'
    return '', 'NO_AUTOMATIC_CAPTION'


def checked_inputs(proposals: Path, frozen: Path) -> tuple[list[dict], str, dict[str, dict]]:
    verify_manifest(proposals.parent)
    verify_manifest(frozen)
    proposal_hash = digest(proposals.read_bytes())
    source_rows = read_csv(proposals)
    fragments = {}
    for row in read_csv(frozen / 'current-schema-snapshot.PRIVATE.csv'):
        if row['kind'] == 'fragment':
            payload = json.loads(row['payload'])
            fragments[str(payload['fragment_id'])] = payload
    images = read_csv(frozen / '0028-image-decisions.UNREVIEWED.csv')
    image_by_identity = {(r['fragment_id'],r['embedded_image_ordinal']):r for r in images}
    identities = [(r['fragment_id'], r['embedded_image_ordinal']) for r in source_rows]
    if len(source_rows) != 72 or len(identities) != len(set(identities)):
        raise ValueError('Expected exactly 72 unique reviewed-source occurrences')
    if set(identities) != {(r['fragment_id'],r['embedded_image_ordinal']) for r in images}:
        raise ValueError('Source image identities differ')
    for r in source_rows:
        frag = fragments.get(r['fragment_id'])
        if not frag or digest((frag.get('text') or '').encode('utf-8')) != r['original_html_sha256']:
            raise ValueError('Original Fragment HTML missing or hash changed')
        original = image_by_identity[(r['fragment_id'],r['embedded_image_ordinal'])]
        if r['original_src_sha256'] != original['original_src_sha256']:
            raise ValueError('Original image source SHA-256 does not match frozen input')
        original_html = frag.get('text') or ''
        extracted, extraction_status = extract_caption(original_html)
        # The proposed caption is a review hint, not the authority: validate it
        # against the frozen, hash-checked HTML before using it as a default.
        if extraction_status == 'UNIQUE_FIGCAPTION' and extracted != r.get('proposal_caption_plaintext_PRIVATE', ''):
            raise ValueError('Proposed caption does not match verified source figcaption')
        if extraction_status == 'NONE' and r.get('proposal_caption_plaintext_PRIVATE', ''):
            raise ValueError('Proposed caption has no original figcaption')
        r['verified_original_caption'] = extracted
        r['verified_caption_status'] = extraction_status
        if any((r.get(k) or '').strip() for k in ('review_disposition','review_occurrence_action','review_page_resolution','review_suffix_mapping','review_text_allocation','review_notes','reviewed_by','reviewed_at')):
            raise ValueError('Proposals unexpectedly contain approved review fields')
    return source_rows, proposal_hash, fragments


def record_key(row: dict) -> str:
    return f"{row['fragment_id']}:{row['embedded_image_ordinal']}"


def browser_data(rows: list[dict], fragments: dict[str, dict]) -> list[dict]:
    out = []
    for row in rows:
        r = {k:row.get(k,'') for k in (
            'fragment_id','embedded_image_ordinal','date','sequence','page_id','marquee_id',
            'page_ownership','triage_priority','candidate_page_context',
            'date_other_page_ids_HINT_ONLY','nearest_before_page_Hint','nearest_after_page_Hint',
            '0024_status','0024_match_method','catalogue_image_id_hint',
            'catalogue_relative_path_hint','catalogue_checksum_hint',
            'file_integrity_status','proposal_disposition_NOT_APPROVED','proposal_state',
            'proposal_caption_plaintext_PRIVATE','verified_original_caption','verified_caption_status',
            'proposal_unallocated_text_PRIVATE',
            'proposal_external_image_hrefs_PRIVATE','proposal_required_checks',
            'original_html_sha256','original_src_sha256',
        )}
        r['key']=record_key(row)
        r['original_html_PRIVATE']=fragments[row['fragment_id']].get('text') or ''
        out.append(r)
    return out


STYLES = r"""
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#202832;background:#f6f8fb}
*{box-sizing:border-box}body{margin:0}header{background:#172b4d;color:white;padding:16px 22px}
header p{margin:6px 0 0;color:#d5e0f1}h1{font-size:1.4rem;margin:0}
.toolbar{padding:12px 22px;background:white;display:flex;gap:10px;flex-wrap:wrap;border-bottom:1px solid #d7dde5}
button,select,input,textarea{font:inherit}button{cursor:pointer;background:#163f78;color:white;border:0;border-radius:5px;padding:8px 12px}
button.alt{background:#e8eef6;color:#18375d}input,select,textarea{border:1px solid #aab8ca;background:white;border-radius:4px;padding:6px;width:100%}
.shell{display:grid;grid-template-columns:310px minmax(0,1fr);min-height:80vh}
aside{background:white;border-right:1px solid #d7dde5;height:calc(100vh - 140px);overflow:auto;position:sticky;top:0}
.item{padding:10px 14px;border-bottom:1px solid #e5e9ee;cursor:pointer;word-break:break-word}
.item:hover,.item.selected{background:#e8f0fc}.item small{color:#586a80;display:block;margin-top:4px}
main{padding:20px;min-width:0;max-width:1100px}section{background:white;border:1px solid #d7dde5;border-radius:6px;padding:15px;margin-bottom:14px}
h2{font-size:1.15rem;margin:0 0 12px}h3{font-size:1rem;margin:12px 0 6px}.kv{display:grid;grid-template-columns:220px 1fr;gap:6px 12px;overflow-wrap:anywhere}
.kv .name{color:#596a7e}.fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.fields label{display:block;font-size:.91rem;color:#42546a}.fields label>span{display:block;margin-bottom:5px}
.fields .wide{grid-column:1/-1}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6fa;border:1px solid #e0e6ed;border-radius:5px;padding:12px;font-size:.83rem;max-height:320px;overflow:auto}
.notice{border-left:4px solid #bd6e13;background:#fff8e8;padding:10px 14px;margin-bottom:14px}
.privacy{font-weight:bold}.status{font-weight:600}.error{color:#a52323}.quiet{color:#586a80}
@media(max-width:800px){.shell{display:block}aside{height:220px;position:static}.kv{grid-template-columns:1fr}.fields{grid-template-columns:1fr}}
"""

JS = r"""
const source = JSON.parse(document.getElementById('source-json').textContent);
const state = Object.fromEntries(source.rows.map(r => [r.key, {}]));
let selected = source.rows[0].key;
const decisionFields = ['disposition','occurrence_action','approved_page_id','page_provenance',
  'suffix_verified','marquee_handling','link_handling','caption_override',
  'text_allocation','review_note','reviewed_by','reviewed_at'];
function currentCaption(row){
  const chosen=(state[row.key].caption_override||'').trim();
  if(chosen)return [chosen,'REVIEWER_OVERRIDE'];
  if(row.verified_caption_status==='UNIQUE_FIGCAPTION')
    return [row.verified_original_caption,'EXISTING_FIGCAPTION'];
  return ['','NO_AUTOMATIC_CAPTION'];
}
function captionPreview(row){
  const [value,origin]=currentCaption(row);
  setText('caption-preview',`Resolved caption: ${value || '(none — needs explicit review)'} [${origin}]`);
}
function beginReview(row){
  const st=state[row.key];
  if(!st.reviewed_by){st.reviewed_by=byId('global-reviewer').value.trim();}
  if(!st.reviewed_at){st.reviewed_at=new Date().toISOString();}
}

const byId = id => document.getElementById(id);
const setText = (id, value) => {byId(id).textContent = String(value ?? '');};
function create(tag, parent, text, className) {
  const node=document.createElement(tag); if (text !== undefined) node.textContent=String(text);
  if(className)node.className=className;parent.appendChild(node);return node;
}
function refreshList(){
  const filter=byId('filter').value;
  const term=byId('search').value.trim().toLowerCase();
  const list=byId('queue');list.replaceChildren();
  for(const r of source.rows){
    const st=state[r.key];
    const isAmbiguous=r['0024_status'] !== 'MATCHED_ONE_IMAGE';
    const isUnowned=!r.page_id;
    const linked=Boolean(r.proposal_external_image_hrefs_PRIVATE);
    if(filter==='ambiguous' && !isAmbiguous)continue;
    if(filter==='unowned' && !isUnowned)continue;
    if(filter==='linked' && !linked)continue;
    if(filter==='ready' && !st.disposition)continue;
    if(term && !(`${r.fragment_id} ${r.date} ${r.catalogue_relative_path_hint}`).toLowerCase().includes(term))continue;
    const item=create('div',list,`Fragment ${r.fragment_id} · ${r.date}`,'item'+(r.key===selected?' selected':''));
    create('small',item, `${r.triage_priority} · ${st.disposition || 'UNREVIEWED'}`);
    item.tabIndex=0;
    item.addEventListener('click',()=>{selected=r.key;render();refreshList()});
    item.addEventListener('keydown',e=>{if(e.key==='Enter'){selected=r.key;render();refreshList()}});
  }
  const count=source.rows.filter(r=>Boolean(state[r.key].disposition)).length;
  setText('progress',`${count}/72 have a draft disposition (not approved for migration)`);
}
function selectField(parent, name, label, options, row){
  const wrap=create('label',parent);create('span',wrap,label);
  const node=create('select',wrap);node.name=name;
  for(const [v,t] of options){const option=create('option',node,t);option.value=v;}
  node.value=state[row.key][name] || '';
  node.addEventListener('change',()=>{
    if(node.value)beginReview(row);
    state[row.key][name]=node.value;
    if(node.value){render();}
    refreshList();
  });
}
function textField(parent,name,label,row,wide=false){
  const wrap=create('label',parent,undefined,wide?'wide':'');create('span',wrap,label);
  const node=name==='review_note'||name==='page_provenance'||name==='text_allocation' ? create('textarea',wrap):create('input',wrap);
  node.name=name;
  node.value=state[row.key][name]|| (name==='reviewed_by' ? byId('global-reviewer').value.trim() : '');
  if(node.tagName==='TEXTAREA')node.rows=2;
  if(name==='caption_override')node.placeholder='Leave blank to use the original caption';
  node.addEventListener('input',()=>{
    if(name==='reviewed_by')byId('global-reviewer').value=node.value;
    if(name!=='reviewed_at' && node.value)beginReview(row);
    state[row.key][name]=node.value;
    if(name==='caption_override')captionPreview(row);
    // Keep the new timestamp visible without overwriting intentional manual edits.
    const timeField=formElement('reviewed_at');
    if(timeField && name!=='reviewed_at')timeField.value=state[row.key].reviewed_at||'';
  });
}
function formElement(name){return Array.from(byId('fields').querySelectorAll('input,textarea,select')).find(x=>x.name===name);}
function render(){
  const row=source.rows.find(r=>r.key===selected);if(!row)return;
  setText('heading',`Fragment ${row.fragment_id} · ${row.date} · image #${row.embedded_image_ordinal}`);
  const facts=byId('facts');facts.replaceChildren();
  for(const [name,val] of [
    ['Page ID (existing)',row.page_id||'(missing)'],['Marquee ID',row.marquee_id||'(missing)'],
    ['Context hint ONLY',row.candidate_page_context],['Other Pages on date',row.date_other_page_ids_HINT_ONLY],
    ['Adjacent Page IDs (hints)',`${row.nearest_before_page_Hint} / ${row.nearest_after_page_Hint}`],
    ['0024 Image ID hint',row.catalogue_image_id_hint||'(ambiguous)'],
    ['0024 File path hint',row.catalogue_relative_path_hint||'(ambiguous)'],
    ['Catalogue integrity',row.file_integrity_status],['0024 matching',row['0024_status']+' / '+row['0024_match_method']],
    ['Proposed outcome (unapproved)',row.proposal_disposition_NOT_APPROVED],
    ['Blockers',row.proposal_required_checks],
    ['External image link targets',row.proposal_external_image_hrefs_PRIVATE||'(none)'],
    ['Original caption (verified)',row.verified_original_caption||'(none)'],
    ['Caption extraction',row.verified_caption_status],
    ['Other unallocated text',row.proposal_unallocated_text_PRIVATE||'(none)']]){
    create('div',facts,name,'name');create('div',facts,val);
  }
  setText('original',row.original_html_PRIVATE);
  const form=byId('fields');form.replaceChildren();
  selectField(form,'disposition','Disposition (explicit review required)',[
    ['','— not reviewed —'],['CONVERT_TO_IMAGE','CONVERT_TO_IMAGE'],['SPLIT_MARQUEE_AND_IMAGE','SPLIT_MARQUEE_AND_IMAGE'],['KEEP_LEGACY','KEEP_LEGACY'],['DEFER','DEFER']],row);
  selectField(form,'occurrence_action','Embedded image action',[
    ['','— not reviewed —'],['REMOVE_AS_IMAGE','REMOVE_AS_IMAGE'],['KEEP_INLINE','KEEP_INLINE'],['DEFER','DEFER']],row);
  textField(form,'approved_page_id','Approved Page ID (if ownership missing)',row);
  textField(form,'page_provenance','Authoritative Page ownership evidence (not date hint)',row,true);
  selectField(form,'suffix_verified','Independent suffix Image ID/path/checksum review',[
    ['','— not reviewed —'],['YES','YES · independently checked'],['NO','NO / cannot verify']],row);
  selectField(form,'marquee_handling','Original Marquee handling',[
    ['','— not reviewed —'],['REMOVE_CONFIRMED','REMOVE confirmed; geometry accepted'],['PRESERVE','PRESERVE Marquee'],['NOT_APPLICABLE','No Marquee']],row);
  selectField(form,'link_handling','Original clickable image hyperlink',[
    ['','— not reviewed —'],['PRESERVE_LEGACY','Keep legacy interactive HTML'],['NOT_PRESENT','No image-wrapping link'],['SUPPORTED_LOSSLESS','Only after tested first-class click support']],row);
  textField(form,'caption_override','Caption override (blank = verified original figcaption)',row,true);
  const preview=create('p',form,undefined,'wide quiet');preview.id='caption-preview';
  captionPreview(row);
  textField(form,'text_allocation','Other text / non-caption content retention plan (if needed)',row,true);
  textField(form,'review_note','Reason for decision, unresolved work and testing notes',row,true);
  textField(form,'reviewed_by','Reviewer identity',row);
  textField(form,'reviewed_at','Review UTC timestamp (ISO 8601)',row);
}
function exportJson(){
  const payload={schema:'0028-human-review-v1',source_sha256:source.source_sha256,
    source_inventory_sha256:source.inventory_sha256,generated_utc:new Date().toISOString(),
    decisions:source.rows.map(r=>({fragment_id:r.fragment_id,embedded_image_ordinal:r.embedded_image_ordinal,
      original_html_sha256:r.original_html_sha256,original_src_sha256:r.original_src_sha256,
      ...Object.fromEntries(decisionFields.map(k=>[k,state[r.key][k]||''])),
      caption_effective:currentCaption(r)[0],caption_source:currentCaption(r)[1]}))};
  const data=new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json'});
  const link=document.createElement('a');link.href=URL.createObjectURL(data);
  link.download='0028-human-review.DRAFT.PRIVATE.json';link.click();URL.revokeObjectURL(link.href);
  setText('message','Draft exported. Keep it private; no database work is authorised.');
}
function importJson(file){
  if(!file)return;
  const reader=new FileReader();reader.onload=()=>{
    try{
      const p=JSON.parse(reader.result);
      if(p.schema!=='0028-human-review-v1'||p.source_sha256!==source.source_sha256||
         p.source_inventory_sha256!==source.inventory_sha256||!Array.isArray(p.decisions)||p.decisions.length!==72)
        throw Error('Wrong schema, input fingerprint or row count');
      const seen=new Set();
      for(const d of p.decisions){
        const k=`${d.fragment_id}:${d.embedded_image_ordinal}`;
        const ref=source.rows.find(r=>r.key===k);
        if(!ref||seen.has(k)||ref.original_html_sha256!==d.original_html_sha256||
           ref.original_src_sha256!==d.original_src_sha256)throw Error('Unexpected/duplicate/changed identity');
        seen.add(k);
      }
      for(const d of p.decisions){
        const key=`${d.fragment_id}:${d.embedded_image_ordinal}`;
        state[key]=Object.fromEntries(decisionFields.map(k=>[k,d[k]||'']));
      }
      const savedReviewer=p.decisions.findLast(d=>Boolean(d.reviewed_by));
      if(savedReviewer && !byId('global-reviewer').value.trim())
        byId('global-reviewer').value=savedReviewer.reviewed_by;
      render();refreshList();setText('message','Existing draft loaded. Reviewer identity restored; validate with Python before approval.');
    }catch(e){setText('message','Import rejected: '+e.message);}
  };reader.readAsText(file);
}
byId('stamp').addEventListener('click',()=>{const name=byId('global-reviewer').value.trim();
  if(!name){setText('message','Enter reviewer name/ID before stamping.');return;}
  state[selected].reviewed_by=name;state[selected].reviewed_at=new Date().toISOString();
  render();setText('message','Stamped selected row at the current UTC time; disposition remains a manual choice.');
});
byId('export').addEventListener('click',exportJson);
byId('import').addEventListener('change',e=>importJson(e.target.files[0]));
byId('search').addEventListener('input',refreshList);
byId('filter').addEventListener('change',refreshList);
refreshList();render();
"""


def make_html(rows: list[dict], proposal_hash: str, inventory_hash: str, fragments: dict[str, dict]) -> str:
    packed=json.dumps({'schema':SCHEMA,'source_sha256':proposal_hash,
                       'inventory_sha256':inventory_hash,'rows':browser_data(rows,fragments)},ensure_ascii=False)
    # Escape *all* HTML script end delimiters and entity/metacharacters.
    packed=packed.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; form-action 'none'; object-src 'none'; base-uri 'none'">
<title>0028 — PRIVATE offline human review</title><style>'''+STYLES+'''</style></head><body>
<header><h1>0028 · Legacy image migration review</h1>
<p class="privacy">PRIVATE · OFFLINE · UNAPPROVED · NO AUTOMATIC CONVERSIONS</p></header>
<div class="toolbar"><input id="search" placeholder="Filter by ID, date or file" style="max-width:240px">
<select id="filter" style="max-width:200px"><option value="all">All 72</option>
<option value="ambiguous">Ambiguous image</option><option value="unowned">Missing Page</option>
<option value="linked">Original image hyperlink</option><option value="ready">With draft disposition</option></select>
<input id="global-reviewer" placeholder="Reviewer name / ID" style="max-width:190px">
<button id="stamp">Stamp selected row</button><button id="export">Export PRIVATE JSON draft</button><label>Import existing draft <input type="file" id="import" accept=".json,application/json"></label>
<span id="progress" class="status"></span></div>
<div class="shell"><aside id="queue" aria-label="Candidate list"></aside><main>
<div class="notice">Do not treat date-neighbour Page hints or UNIQUE_LOCAL_SUFFIX matches as approval. The current reader does not preserve an image-wrapping external link on IMAGE media. No review choice here executes migration. Save your draft regularly.</div>
<p id="message" class="quiet" aria-live="polite"></p><section><h2 id="heading"></h2>
<div id="facts" class="kv"></div><h3>Original HTML — shown as inert text (never executed)</h3><pre id="original"></pre></section>
<section><h2>Explicit manual decisions</h2><div id="fields" class="fields"></div></section>
</main></div><script id="source-json" type="application/json">'''+packed+'''</script><script>'''+JS+'''</script></body></html>'''


def write_with_checksums(out: Path, files: dict[str, bytes]) -> None:
    if out.exists():
        raise ValueError('Refusing to overwrite an existing evidence directory')
    out.mkdir(parents=True,mode=0o700)
    lines=[]
    for name, data in files.items():
        dest=out/name;dest.write_bytes(data);dest.chmod(0o600)
        lines.append(f'{digest(data)}  {name}')
    (out/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (out/'SHA256SUMS.txt').chmod(0o600)


def assess_decisions(rows: list[dict], proposal_sha: str, inventory_sha: str, payload: dict) -> dict:
    if payload.get('schema')!=SCHEMA or payload.get('source_sha256')!=proposal_sha or payload.get('source_inventory_sha256')!=inventory_sha:
        raise ValueError('Draft schema or evidence source fingerprint mismatch')
    proposed={record_key(r):r for r in rows}
    given=payload.get('decisions')
    if not isinstance(given,list) or len(given)!=len(rows):
        raise ValueError('Missing or extra decision rows')
    seen=set();counts=Counter();issues=Counter();review=[]
    for d in given:
        key=record_key(d)
        if key in seen or key not in proposed:
            raise ValueError('Duplicate or unknown decision identity')
        seen.add(key);r=proposed[key]
        if d.get('original_html_sha256')!=r['original_html_sha256'] or d.get('original_src_sha256')!=r['original_src_sha256']:
            raise ValueError('Source hash or embedded image identity changed')
        decision=(d.get('disposition') or '').strip()
        action=(d.get('occurrence_action') or '').strip()
        blocked=[]
        if decision not in DECISIONS: blocked.append('NO_REVIEWED_DISPOSITION')
        if action not in ACTIONS: blocked.append('NO_OCCURRENCE_ACTION')
        if not (d.get('reviewed_by') or '').strip():blocked.append('MISSING_REVIEWER')
        if not (d.get('reviewed_at') or '').strip():blocked.append('MISSING_REVIEW_TIMESTAMP')
        else:
            try:
                stamp=datetime.fromisoformat(d['reviewed_at'].replace('Z','+00:00'))
                if stamp.tzinfo is None: raise ValueError()
            except (ValueError,TypeError): blocked.append('INVALID_REVIEW_TIMESTAMP')
        if not (d.get('review_note') or '').strip():blocked.append('MISSING_REVIEW_REASON')
        caption_override = d.get('caption_override') or ''
        if not isinstance(caption_override, str) or len(caption_override) > 2000:
            blocked.append('INVALID_CAPTION_OVERRIDE')
            caption_override = ''
        effective_caption, caption_source = resolve_caption(r, caption_override)
        # New drafts export the resolved value; recompute from trusted source.
        # Older v1 drafts without these fields remain importable/checkable.
        if 'caption_effective' in d and d['caption_effective'] != effective_caption:
            blocked.append('CAPTION_RESOLUTION_MISMATCH')
        if 'caption_source' in d and d['caption_source'] != caption_source:
            blocked.append('CAPTION_SOURCE_MISMATCH')
        if decision=='DEFER':
            if action!='DEFER':blocked.append('DEFER_ACTION_MISMATCH')
        elif decision=='KEEP_LEGACY':
            if action!='KEEP_INLINE':blocked.append('KEEP_LEGACY_ACTION_MISMATCH')
        elif decision in ('CONVERT_TO_IMAGE','SPLIT_MARQUEE_AND_IMAGE'):
            if action!='REMOVE_AS_IMAGE':blocked.append('REMOVE_ACTION_REQUIRED')
            if r['0024_status']!='MATCHED_ONE_IMAGE' or r['catalogue_cross_check']!='MATCHED_SNAPSHOT_AND_FILE':
                blocked.append('UNRESOLVED_IMAGE')
            if d.get('suffix_verified')!='YES':blocked.append('SUFFIX_NOT_INDEPENDENTLY_VERIFIED')
            if not r['page_id']:
                try:
                    if int(d.get('approved_page_id') or '0')<=0:raise ValueError()
                except ValueError: blocked.append('NO_AUTHORISED_PAGE_ID')
                if not (d.get('page_provenance') or '').strip():blocked.append('NO_PAGE_PROVENANCE')
            if r['proposal_external_image_hrefs_PRIVATE']:
                # No current IMAGE renderer support; never bless lost hyperlink click behaviour.
                blocked.append('IMAGE_LINK_PRESERVATION_NOT_IMPLEMENTED')
            elif d.get('link_handling')!='NOT_PRESENT':
                blocked.append('LINK_ABSENCE_NOT_CONFIRMED')
            if r['marquee_id'] and decision=='CONVERT_TO_IMAGE' and d.get('marquee_handling')!='REMOVE_CONFIRMED':
                blocked.append('MARQUEE_REMOVAL_NOT_APPROVED')
            if decision=='SPLIT_MARQUEE_AND_IMAGE' and not r['marquee_id']:
                blocked.append('SPLIT_REQUIRES_REAL_MARQUEE')
            if not effective_caption and r.get('verified_caption_status') == 'REQUIRES_MANUAL_REVIEW':
                blocked.append('AMBIGUOUS_CAPTION_REQUIRES_MANUAL_REVIEW')
            # A single verified, plain caption is retained by default in the
            # review contract. Other prose, stray text, markup and bare-image
            # cases must still have an explicit reviewer allocation/acknowledgement.
            if (not (d.get('text_allocation') or '').strip() and
                (bool(r.get('proposal_unallocated_text_PRIVATE')) or not effective_caption or
                 int(r.get('proposal_caption_link_count') or '0') > 0)):
                blocked.append('TEXT_ALLOCATION_UNREVIEWED_OR_EMPTY_NOT_ACKNOWLEDGED')
        else:
            if action and action not in ACTIONS:blocked.append('BAD_ACTION')
        counts[decision or 'UNREVIEWED']+=1
        for reason in blocked:issues[reason]+=1
        review.append({'key':key,'disposition':decision,'blockers':blocked})
    return {'status':'DRAFT_REVIEW_ONLY','count':len(rows),'byDisposition':dict(sorted(counts.items())),
            'blockers':dict(sorted(issues.items())),
            'rowsWithBlockers':sum(bool(x['blockers']) for x in review),
            'explicitReviewerDecisions':sum(x['disposition'] in DECISIONS and not x['blockers'] for x in review),
            'migrationApproved':False,'productionApplyAllowed':False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('build','check'))
    p.add_argument('--proposals',type=Path,required=True,help='Private unapproved proposed-review CSV')
    p.add_argument('--frozen',type=Path,required=True,help='Verified frozen 0028 evidence directory')
    p.add_argument('--decisions',type=Path,help='Exported manual decision JSON, check mode')
    p.add_argument('--output',type=Path,required=True,help='New private output directory')
    a=p.parse_args(argv)
    rows,ph,fragments=checked_inputs(a.proposals,a.frozen)
    invhash=digest((a.frozen/'current-schema-snapshot.PRIVATE.csv').read_bytes())
    if a.mode=='build':
        if a.decisions: p.error('--decisions is only accepted in check mode')
        html_page=make_html(rows,ph,invhash,fragments).encode('utf-8')
        summary={'status':'PRIVATE_UNAPPROVED_PORTAL','candidates':len(rows),
                 'sourceSha256':ph,'frozenInventorySha256':invhash,'approval':None,
                 'productionApplyAllowed':False}
        write_with_checksums(a.output,{'0028-offline-review.PRIVATE.html':html_page,
                                      '0028-review-portal-summary.json':(json.dumps(summary,indent=2)+'\n').encode()})
        print('PASS: PRIVATE offline review portal created; 72 decisions still unapproved')
    else:
        if not a.decisions:p.error('--decisions required in check mode')
        payload=json.loads(a.decisions.read_text(encoding='utf-8'))
        summary=assess_decisions(rows,ph,invhash,payload)
        write_with_checksums(a.output,{'0028-review-draft-check.json':(json.dumps(summary,indent=2)+'\n').encode()})
        print(f"PASS: DRAFT CHECK completed; {summary['rowsWithBlockers']} rows still blocked; apply NEVER authorised")
    print(f'Evidence stored privately: {a.output}')

if __name__=='__main__':
    main()

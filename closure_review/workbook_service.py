"""HTTP-facing workbook orchestration; files remain in request memory."""
import base64
import binascii
import csv
from io import BytesIO
from . import engine
from .workbooks import inspect_workbook, map_workbook


def decode(payload):
    if not isinstance(payload, dict):
        raise ValueError('Provide a workbook file and mapping.')
    encoded = payload.get('content_base64')
    if not isinstance(encoded, str) or len(encoded) > 10_700_000:
        raise ValueError('Select an XLSX file smaller than 8 MB.')
    try:
        return base64.b64decode(encoded, validate=True), payload.get('filename')
    except (ValueError, binascii.Error):
        raise ValueError('Workbook upload is not valid base64.') from None


def inspect(payload):
    return inspect_workbook(*decode(payload))


def mapped(payload):
    return map_workbook(*decode(payload), payload.get('mapping'))


def compare(payload):
    before, after = mapped(payload.get('baseline')), mapped(payload.get('current'))
    if not before['can_compare'] or not after['can_compare']:
        raise ValueError('Resolve every workbook blocker before comparing. No partial estimate was compared.')
    result = engine.compare_csv(before['csv'], after['csv'])
    maps = [{p['id']:p for p in v['provenance']} for v in (before, after)]
    before_rows={r['id']:r for r in before['rows']}
    after_rows={r['id']:r for r in after['rows']}
    provenance_only=set()
    for row in result['rows']:
        old,new=before_rows.get(row['id']),after_rows.get(row['id'])
        if old and new and all(old[k]==new[k] for k in ('activity','quantity','unit','rate')):
            row['status']='unchanged'
            row['evidence_changed']=old['source']!=new['source']
            if row['evidence_changed']:provenance_only.add(row['id'])
    result['findings']=[f for f in result['findings'] if f['id'] not in provenance_only]
    result['provenance_updates']=len(provenance_only)
    for row in result['rows']:
        row['baseline_provenance'] = maps[0].get(row['id'])
        row['current_provenance'] = maps[1].get(row['id'])
    issues = sum(len(v['issues']) for v in (before, after))
    return {'comparison':result, 'mode':'workbooks',
        'sources':[{'title':v['filename'], 'note': 'Explicitly mapped workbook. File SHA256 '+v['sha256'],
                    'mapping':v['mapping'], 'issues':v['issues'], 'provenance':v['provenance']} for v in (before, after)],
        'workbook_checks':{'warnings':issues, 'baseline':before['summary'], 'current':after['summary']}}


def sample(version):
    from openpyxl import Workbook
    w=Workbook();s=w.active;s.title='Closure schedule'
    s.append(['ILLUSTRATIVE WORKBOOK — NOT A COMPANY REVISION'])
    s.append(['Prepared from historical category totals for import testing. Rates and areas are reconstructed.'])
    s.append([])
    s.append(['Activity code','Work description','Costed quantity','Unit','Rate USD','Stated cost USD'])
    for row in csv.DictReader(engine.template('baseline' if version=='baseline' else 'current').splitlines()):
        q,r=float(row['quantity']),float(row['rate'])
        s.append([row['id'],row['activity'],q,row['unit'],r,q*r])
    s.append(['TOTAL','Total selected activities',None,None,None,sum(s.cell(i,6).value for i in range(5,13))])
    for col in ['A','B','C','D','E','F']:s.column_dimensions[col].width=24 if col!='B' else 42
    out=BytesIO();w.save(out);return out.getvalue()

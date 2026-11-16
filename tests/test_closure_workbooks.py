import base64
import io
import unittest
from openpyxl import Workbook
from closure_review.workbooks import inspect_workbook,map_workbook
from closure_review.workbook_service import sample,compare

MAPPING={'sheet':'Closure schedule','header_row':4,'start_row':5,'end_row':13,'exclude_rows':[13], 'columns':{'id':'A','activity':'B','quantity':'C','unit':'D','rate':'E','cost':'F'},'currency':'USD','basis':'undiscounted'}

def book(rows):
    w=Workbook();s=w.active;s.title='Costs';s.append(['ID','Activity','Qty','Unit','Rate','Cost'])
    for row in rows:s.append(row)
    out=io.BytesIO();w.save(out);return out.getvalue()

def mapping(end):
    return {**MAPPING,'sheet':'Costs','header_row':1,'start_row':2,'end_row':end,'exclude_rows':[]}

class WorkbookTests(unittest.TestCase):
    def test_sample_lineage_and_reconciliation(self):
        before=sample('baseline');after=sample('current')
        inspection=inspect_workbook(before,'baseline.xlsx')
        self.assertEqual(inspection['sheets'][0]['header_candidates'][0]['row'],4)
        mapped=map_workbook(before,'baseline.xlsx',MAPPING)
        self.assertTrue(mapped['can_compare']);self.assertEqual(mapped['summary']['included'],8)
        self.assertEqual(mapped['provenance'][0]['cells']['quantity'],'C5')
        def payload(raw,name):return {'content_base64':base64.b64encode(raw).decode(),'filename':name,'mapping':MAPPING}
        result=compare({'baseline':payload(before,'before.xlsx'),'current':payload(after,'after.xlsx')})
        self.assertEqual(result['comparison']['delta'],191830)
        self.assertEqual(result['comparison']['rows'][0]['baseline_provenance']['cells']['rate'],'E5')
        self.assertEqual(result['mode'],'workbooks')
        self.assertEqual(len(result['comparison']['findings']),4)
        self.assertTrue(result['comparison']['rows'][0]['evidence_changed'])

    def test_subtotal_blocks_until_explicitly_excluded(self):
        content=sample('baseline');m={**MAPPING,'exclude_rows':[]};r=map_workbook(content,'test.xlsx',m)
        self.assertFalse(r['can_compare']);self.assertIsNone(r['csv'])
        self.assertIn('subtotal_row',[x['code'] for x in r['issues']])

    def test_missing_formula_cache_and_mismatched_cost(self):
        r=map_workbook(book([['x','Soil',2,'ha',10,'=C2*E2']]),'test.xlsx',mapping(2))
        self.assertFalse(r['can_compare']);self.assertIn('missing_formula_cache',[x['code'] for x in r['issues']])
        r=map_workbook(book([['x','Soil',2,'ha',10,25]]),'test.xlsx',mapping(2))
        self.assertIn('cost_mismatch',[x['code'] for x in r['issues']])

    def test_duplicate_and_missing_inputs_do_not_become_zero(self):
        r=map_workbook(book([['x','Soil',None,'ha',10,0],['x','Other',0,'ha',10,0]]),'test.xlsx',mapping(3))
        self.assertFalse(r['can_compare']);codes=[x['code'] for x in r['issues']]
        self.assertIn('duplicate_id',codes);self.assertIn('invalid_number',codes)

    def test_zero_valid_and_no_partial_comparison(self):
        r=map_workbook(book([['x','Soil',0,'ha',10,0]]),'test.xlsx',mapping(2))
        self.assertTrue(r['can_compare']);self.assertEqual(r['rows'][0]['quantity'],0)
        bad=base64.b64encode(book([['x','Soil',None,'ha',10,0]])).decode()
        with self.assertRaises(ValueError):compare({'baseline':{'filename':'bad.xlsx','content_base64':bad,'mapping':mapping(2)},'current':{'filename':'bad.xlsx','content_base64':bad,'mapping':mapping(2)}})

    def test_excel_error_in_text_column_is_blocked(self):
        content=book([['x','#REF!',2,'ha',10,20]])
        result=map_workbook(content,'test.xlsx',mapping(2))
        self.assertFalse(result['can_compare'])
        self.assertIn('excel_error',[x['code'] for x in result['issues']])

    def test_bad_archive_size_and_mapping(self):
        for raw,name in [(b'not zip','bad.xlsx'),(b'x'*8000001,'big.xlsx'),(sample('baseline'),'file.xlsm')]:
            with self.assertRaises(ValueError):inspect_workbook(raw,name)
        with self.assertRaises(ValueError):map_workbook(sample('baseline'),'x.xlsx',{**MAPPING,'currency':'AUD'})
        with self.assertRaises(ValueError):map_workbook(sample('baseline'),'x.xlsx',{**MAPPING,'columns':{**MAPPING['columns'],'rate':'C'}})

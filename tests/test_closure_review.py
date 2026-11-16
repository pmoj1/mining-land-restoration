import unittest
from closure_review.engine import compare_csv, demo, parse_csv, template


class ClosureComparisonTests(unittest.TestCase):
    def test_public_baseline_and_driver_reconciliation(self):
        c = demo()['comparison']
        self.assertEqual(c['baseline_total'], 4091620)
        self.assertEqual(c['current_total']-c['baseline_total'], c['quantity_effect']+c['rate_effect'])
        self.assertEqual(c['quantity_effect'], 54000)
        self.assertEqual(c['rate_effect'], 137830)

    def test_identical_files_have_no_findings(self):
        c = compare_csv(template('baseline'), template('baseline'))
        self.assertEqual(c['delta'], 0)
        self.assertEqual(c['findings'], [])

    def test_empty_missing_duplicate_and_bad_numbers_rejected(self):
        header='id,activity,quantity,unit,rate,source\n'
        cases=[header,header+'x,Task,,ha,5,source\n',header+'x,Task,1,ha,5,source\nx,Task,2,ha,5,source\n']
        for number in ['NaN','Infinity','-1','no','1000000000001','0.0000001']:
            cases.append(header+f'x,Task,{number},ha,5,source\n')
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError): parse_csv(case)

    def test_unit_mismatch_rejected(self):
        baseline=template('baseline')
        with self.assertRaisesRegex(ValueError,'units differ'):
            compare_csv(baseline,baseline.replace(',ha,',',m2,',1))

    def test_added_removed_keep_missing_values_explicit(self):
        header='id,activity,quantity,unit,rate,source\n'
        c=compare_csv(header+'x,Old,2,ha,10,source\n',header+'y,New,3,ha,12,source\n')
        self.assertEqual(c['delta'],16)
        self.assertIsNone(c['rows'][0]['current_quantity'])
        self.assertIsNone(c['rows'][1]['baseline_rate'])
        self.assertEqual([r['status'] for r in c['rows']],['removed','added'])

    def test_zero_is_valid(self):
        text='id,activity,quantity,unit,rate,source\nx,Task,0,ha,0,source\n'
        self.assertEqual(compare_csv(text,text)['baseline_total'],0)

    def test_decimal_calculation(self):
        header='id,activity,quantity,unit,rate,source\n'
        c=compare_csv(header+'x,Task,0.1,ha,0.2,s\n',header+'x,Task,0.3,ha,0.4,s\n')
        self.assertEqual(c['delta'],0.1)


if __name__=='__main__': unittest.main()

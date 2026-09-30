"""Regression checks against archived outputs and manuscript numeric tables."""
from pathlib import Path
import json
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

class ReproductionChecks(unittest.TestCase):
    def test_archived_primary_results(self):
        saved=pd.read_csv(ROOT/'reference/primary_metrics_archived.csv').set_index('participant_id')
        current=pd.read_csv(ROOT/'results/primary_metrics.csv')
        for model,suffix in [('ConstDecel','cd'),('SafeEnv','safeenv'),('CGP','cgp')]:
            actual=current.query('model == @model').set_index('participant_id').loc[saved.index]
            for metric in ['MAE','MSE']:
                np.testing.assert_allclose(actual[metric],saved[f'{metric.lower()}_{suffix}'],rtol=0,atol=1e-10)

    def test_tables_at_reported_precision(self):
        expected={
            'table2_primary':[[4.47,4.10,30.30,24.76],[3.52,3.17,23.06,15.73],[2.28,1.78,15.87,7.57]],
            'table5_ablation':[[2.28,1.78,15.87,7.57],[2.73,2.08,20.47,11.04],[2.60,2.00,18.66,10.69]],
            'table6_downsampling':[[2.28,1.78,15.87,7.57],[2.26,1.77,15.64,7.99]]}
        for name,values in expected.items():
            actual=pd.read_csv(ROOT/f'results/{name}.csv')
            np.testing.assert_array_equal(actual[['mae_mean','mae_median','mse_mean','mse_median']].round(2),values)
        acceleration=pd.read_csv(ROOT/'results/table4_acceleration.csv').iloc[:,1:]
        np.testing.assert_array_equal(acceleration.round(2),[[-18.90,-1.33,.25,-33.62,18.57],[-17.72,-1.34,0,-19.71,0]])

    def test_constraints_and_counts(self):
        checks=pd.read_csv(ROOT/'results/table3_constraints.csv').set_index('constraint')
        self.assertEqual(checks.violations.to_dict(),{'C1':0,'C2':0,'C3':36,'C4':0})
        self.assertEqual(checks.samples.to_dict(),{'C1':3354,'C2':3354,'C3':3322,'C4':3354})
        wins=pd.read_csv(ROOT/'results/win_rates.csv').set_index(['baseline','metric'])
        self.assertEqual(wins.loc[('SafeEnv','MAE'),'wins'],26)
        self.assertEqual(wins.loc[('SafeEnv','MSE'),'wins'],25)

    def test_data_integrity_and_release_scope(self):
        trajectory=pd.read_csv(ROOT/'data/trajectories.csv')
        survey=pd.read_csv(ROOT/'data/survey_covariates.csv')
        self.assertEqual(len(trajectory),7151)
        self.assertEqual(len(survey),32)
        self.assertTrue(survey.participant_id.is_unique)
        self.assertEqual(set(trajectory.participant_id),set(survey.participant_id))
        self.assertTrue(trajectory.participant_id.str.fullmatch(r'P\d{3}').all())
        self.assertFalse(trajectory.isna().any().any())
        self.assertFalse(survey.isna().any().any())
        self.assertTrue((survey.yrs_drive<=survey.age).all())
        self.assertEqual(survey.yrs_drive.max(),16)
        self.assertFalse(list(ROOT.rglob('*.xlsx')))
        self.assertFalse(list(ROOT.rglob('*participant_id_mapping*')))
        geometry=json.loads((ROOT/'data/geometry.json').read_text())
        self.assertEqual(geometry['stop_line_coord2_ft'],1074)
        features=pd.read_csv(ROOT/'results/discussion_features.csv')
        np.testing.assert_array_equal(features.t2_hat,features.t2_reconstruction)

if __name__=='__main__':unittest.main()

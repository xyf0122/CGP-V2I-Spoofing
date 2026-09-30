"""Reproduce deterministic ESWA reconstruction tables from released inputs.

Run from any directory: python path/to/scripts/reproduce.py
All paths resolve relative to this repository; no original archive is needed.
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import cgp


def approach(group, step=1):
    group = group.sort_values('time').iloc[::step].reset_index(drop=True)
    hit = np.flatnonzero(group.speed.to_numpy() <= cgp.V_STOP)
    endpoint = int(hit[0]) if len(hit) else int(np.argmin(group.speed))
    return group.iloc[:endpoint + 1]


def summarize(frame, group):
    return frame.groupby(group, sort=False).agg(
        mae_mean=('MAE', 'mean'), mae_median=('MAE', 'median'),
        mse_mean=('MSE', 'mean'), mse_median=('MSE', 'median')).reset_index()


def main():
    output = ROOT / 'results'
    output.mkdir(exist_ok=True)
    geometry = json.loads((ROOT / 'data/geometry.json').read_text())
    stop = geometry['stop_line_coord2_ft'] + geometry['safety_buffer_ft']
    assert stop == 1074.0, 'Reference validation applies to the archived zero-buffer case.'
    trajectories = pd.read_csv(ROOT / 'data/trajectories.csv')
    survey = pd.read_csv(ROOT / 'data/survey_covariates.csv')
    assert len(trajectories) == 7151 and trajectories.participant_id.nunique() == 32
    assert trajectories.notna().all().all()
    assert not trajectories.duplicated(['participant_id', 'time']).any()
    primary, ablation, downsampling, residuals, states, features, compliance = ([] for _ in range(7))
    for participant, group in trajectories.groupby('participant_id'):
        assert np.allclose(np.diff(group.sort_values('time').time), .1)
        for step in (1, 2):
            segment = approach(group, step)
            t = segment.time.to_numpy()
            observed = segment.speed.to_numpy()
            a = segment.accel_1.to_numpy()
            dt = .1 * step
            x0, v0, a0 = -segment.coord_2.iloc[0], observed[0] * cgp.MPH_TO_FTPS, a[0]
            t2, _ = cgp.detect_t2_change_point(t, a, dt=dt)
            t1 = max(0, t2 - cgp.TAU)
            full = cgp.simulate_cgp(t, x0, v0, a0, -stop, t1, t2, dt=dt, return_state=True)
            def errors(prediction):
                residual = prediction * cgp.FTPS_TO_MPH - observed
                return {'MAE': float(np.mean(abs(residual))), 'MSE': float(np.mean(residual ** 2))}
            downsampling.append({'participant_id': participant, 'resolution_hz': 10 // step,
                                 'T_i': float(t[-1]), 't2_hat': t2, **errors(full[:, 1])})
            if step == 2:
                continue
            predictions = {
                'ConstDecel': cgp.simulate_constdecel(t, x0, v0, -stop),
                'SafeEnv': cgp.simulate_safeenv(t, x0, v0, -stop),
                'CGP': full[:, 1]}
            for model, prediction in predictions.items():
                primary.append({'participant_id': participant, 'model': model,
                                'T_i': float(t[-1]), 't2_hat': t2, **errors(prediction)})
                residuals.extend({'participant_id': participant, 'model': model, 'time_s': float(tk),
                                  'observed_mph': float(obs), 'predicted_mph': float(pred * cgp.FTPS_TO_MPH),
                                  'residual_mph': float(pred * cgp.FTPS_TO_MPH - obs), 't2_hat': t2}
                                 for tk, obs, pred in zip(t, observed, prediction))
            for variant, gate, ugm in [('Full', True, True), ('Without gate', False, True), ('Without UGM', True, False)]:
                prediction = cgp.simulate_cgp(t, x0, v0, a0, -stop, t1, t2, gate=gate, ugm=ugm)
                ablation.append({'participant_id': participant, 'variant': variant, **errors(prediction)})
            states.extend({'participant_id': participant, 'time_s': float(tk), 'position_ft': float(x),
                           'speed_ftps': float(v), 'acceleration_ftps2': float(acc),
                           'observed_acceleration_ftps2': float(ao)}
                          for tk, (x, v, acc), ao in zip(t, full, a))
            jerk = np.diff(full[:, 2]) / dt
            checks = [('C1', full[:, 1] < -1e-9),
                      ('C2', (full[:, 2] < -cgp.BAR_ALPHA - 1e-9) | (full[:, 2] > 1e-9)),
                      ('C3', abs(jerk) > cgp.JMAX + 1e-9),
                      ('C4', full[:, 0] > -stop + 1e-9)]
            for name, mask in checks:
                compliance.append({'participant_id': participant, 'constraint': name,
                                   'violations': int(mask.sum()), 'samples': len(mask)})
            # Use the same verified commitment time throughout all analyses.
            td = t2
            d0 = segment.coord_2.iloc[0] - geometry['stop_line_coord2_ft']
            pre, post = a[t < td], a[t >= td]
            features.append({'participant_id': participant, 'T_i': float(t[-1]), 't2_hat': td,
                             't2_reconstruction': t2, 'ttb0': d0 / (observed[0] * 1.4666666667),
                             'slack0': 2 * cgp.BAR_ALPHA * d0 - (observed[0] * 1.4666666667) ** 2,
                             'v0_mph': observed[0], 'd0_ft': d0, 'a_pre': pre.mean(), 'a_post': post.mean(),
                             'da': post.mean() - pre.mean(), 'jerk_p95': np.quantile(abs(np.diff(a) / dt), .95),
                             'vmin_mph': observed.min()})
    frames = dict(primary_metrics=pd.DataFrame(primary), ablation_metrics=pd.DataFrame(ablation),
                  downsampling_metrics=pd.DataFrame(downsampling), trajectory_reconstructions=pd.DataFrame(residuals),
                  simulated_states=pd.DataFrame(states), discussion_features=pd.DataFrame(features),
                  constraint_metrics=pd.DataFrame(compliance))
    frames['table2_primary'] = summarize(frames['primary_metrics'], 'model')
    frames['table5_ablation'] = summarize(frames['ablation_metrics'], 'variant')
    frames['table6_downsampling'] = summarize(frames['downsampling_metrics'], 'resolution_hz')
    constraints = frames['constraint_metrics'].groupby('constraint')[['violations', 'samples']].sum().reset_index()
    constraints['violation_rate'] = constraints.violations / constraints.samples
    frames['table3_constraints'] = constraints
    quantiles = []
    for name, column in [('Observed', 'observed_acceleration_ftps2'), ('CGP', 'acceleration_ftps2')]:
        values = frames['simulated_states'][column]
        quantiles.append(dict(signal=name, p05=values.quantile(.05), p50=values.median(),
                              p95=values.quantile(.95), minimum=values.min(), maximum=values.max()))
    frames['table4_acceleration'] = pd.DataFrame(quantiles)
    saved = pd.read_csv(ROOT / 'reference/primary_metrics_archived.csv').set_index('participant_id')
    differences = []
    wins = []
    for model, suffix in [('ConstDecel', 'cd'), ('SafeEnv', 'safeenv'), ('CGP', 'cgp')]:
        current = frames['primary_metrics'].query('model == @model').set_index('participant_id')
        for metric in ['MAE', 'MSE']:
            difference = (current[metric] - saved[f'{metric.lower()}_{suffix}']).abs().max()
            differences.append(float(difference))
            if model != 'CGP':
                full = frames['primary_metrics'].query('model == "CGP"').set_index('participant_id')
                wins.append(dict(baseline=model, metric=metric, wins=int((full[metric] < current[metric]).sum()), participants=32))
    assert max(differences) < 1e-10, differences
    frames['win_rates'] = pd.DataFrame(wins)
    merged = frames['discussion_features'].merge(survey, on='participant_id', validate='one_to_one').dropna()
    columns = ['t2_hat','ttb0','slack0','v0_mph','d0_ft','a_pre','a_post','da','jerk_p95','vmin_mph']
    correlation = merged[columns].corr()
    original_corr = pd.read_csv(ROOT / 'reference/correlation_coefficients.csv', index_col=0)
    correlation_difference = float(abs(correlation - original_corr).max().max())
    correlation.to_csv(output / 'discussion_correlations.csv')
    covariate_correlations = []
    for name in ['ttb0','v0_mph','yrs_drive','comfort_pre','trust_pre']:
        result = stats.spearmanr(merged.t2_hat, merged[name])
        covariate_correlations.append(dict(covariate=name, spearman_rho=result.statistic, pvalue=result.pvalue, n=len(merged)))
    frames['discussion_rank_correlations'] = pd.DataFrame(covariate_correlations)
    pairs = []
    for metric in ['MAE', 'MSE']:
        paired = frames['downsampling_metrics'].pivot(index='participant_id', columns='resolution_hz', values=metric)
        result = stats.wilcoxon(paired[10], paired[5], method='exact')
        pairs.append(dict(comparison='10 Hz versus 5 Hz', metric=metric, statistic=result.statistic,
                          pvalue=result.pvalue, method='two-sided exact Wilcoxon signed-rank'))
    frames['downsampling_tests'] = pd.DataFrame(pairs)
    for name, frame in frames.items():
        frame.to_csv(output / f'{name}.csv', index=False)
    report = {
        'participants': 32, 'trajectory_rows': 7151,
        'primary_reference_max_absolute_error': max(differences),
        'discussion_correlation_reference_max_absolute_error': correlation_difference,
        'discussion_and_reconstruction_timing_differ_for_n_participants': int((frames['discussion_features'].t2_hat != frames['discussion_features'].t2_reconstruction).sum()),
        'unverified_comparators': ['Clipped IDM', 'Clipped Gipps'],
        'archived_mantel_values': 'Archived rounded values are retained as provenance; rerun discussion.R for corrected analysis.',
        'survey_experience_records_exceeding_age': int((survey.yrs_drive > survey.age).sum())}
    (output / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    for name in ['table2_primary','table3_constraints','table4_acceleration','table5_ablation','table6_downsampling','discussion_rank_correlations']:
        print(name, frames[name].round(6).to_dict('records'))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

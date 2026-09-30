# Reproduction methods

## Reconstruction

For each participant, sort by elapsed time and keep observations through the first speed at or below 0.5 mph. If no such observation exists, use the first minimum-speed sample. At 5 Hz, retain every second observation beginning at time zero and identify the endpoint again on that sequence.

The commitment detector uses the archived Python implementation: centered five-sample averaging with zero padding; minimum regime length 1 s; directional acceleration threshold 0.2 ft/s²; least within-segment squared error among feasible split points. When no directional split exists, select the minimum-error split without that restriction. Ties take the first candidate. The same five-sample window is used at 10 Hz and 5 Hz, corresponding to different durations.

All reconstruction and discussion analyses now use this shared detector. The archived R plots left edge observations unsmoothed, and the earlier appendix described repeated-edge padding. Those alternatives did not generate the manuscript's reconstruction tables.

CGP parameters: planning deceleration 10 ft/s²; maximum deceleration 34 ft/s²; jerk bound 50 ft/s³; latency 0.5 s; scenario reference time 5 s; TTB reference 1.5 s; logistic scale 1 s; urgency weights (0.7, 0.6, 0.4). Initial acceleration is clipped to [-34,0]. The safe stopping target is the stop line, with zero additional buffer. Perceived-risk modulation of planning deceleration is inactive in this empirical instantiation. The acceleration gain uses exp(a), corresponding to a reference acceleration of 1 ft/s².

Post-identification braking demand is computed once from the simulated identification state. CGP uses the safe-speed envelope and acceleration/jerk bounds at each step. When their intersection is empty, the archived implementation prioritizes the speed envelope. This explains the 36 jerk exceedances among 3,322 jerk samples; the reproduced speed, acceleration, and stop-line checks have zero violations.

No-gate ablation sets the commitment indicator to zero; no-UGM ablation sets the gain multiplier to one. The original notebook's numerical operations are preserved in `src/cgp.py`, with optional state recording and these two ablation switches added.

## Supporting analyses

Pre-commitment acceleration averages samples with t < t2; post-commitment acceleration averages t >= t2 through the same near-stop endpoint. Driving experience >=7 years and comfort codes >=4 define the discussion's two subgroup comparisons. The corrected experience value is 10 years, as recorded in the participant's free-text response.

PCA uses standardized commitment time, TTB, initial speed, pre/post acceleration, 95th-percentile absolute jerk, and minimum speed. The first three PCs feed three-cluster k-means with 50 starts and seed 7. PCA axis signs and cluster numbers are arbitrary. The timing scatter plot retains the archived separate clustering definition: standardized commitment time, TTB, initial speed, post-commitment acceleration, jerk, and minimum speed, with the same k-means settings. Its regression is ordinary least squares with a 95% confidence interval for the mean response.

Mantel comparisons use Euclidean distances for each survey block and each individual trajectory feature, Pearson distance correlation, and 999 one-sided permutations for positive distance association. The three blocks are demographics/exposure, pre-experiment attitudes, and post-experiment responses. The release uses explicit base-R seed 123 and a shared permutation matrix. Raw permutation p-values are exploratory and unadjusted across the 30 tests. All reproduced r values are below 0.20; one comparison has nominal p<0.05.

The original `linkET` call left distance arguments at their defaults. The documented [implementation](https://github.com/Hy4m/linkET/blob/master/R/mantel-test.R) selects Euclidean distances for numeric survey blocks if any block contains a zero-sum row, which these data do. The current implementation has a default seed; the archive does not record its installed version. The rerun uses explicit settings, rather than claiming bit-for-bit equivalence to archived rounded permutation p-values.

Paired reconstruction plots use two-sided Wilcoxon signed-rank tests. Exact p-values are used when there are no zero differences or tied absolute differences; otherwise a normal approximation with continuity correction is used. Ablation p-values are adjusted by Benjamini-Hochberg across the three comparisons within each metric. Downsampling has one comparison per metric. Win-rate error bars show one standard error of the participant-level binary indicator.

Figure 7c-d is generated from the corrected downsampling CSV using the original ggplot2 style: Helvetica-compatible embedded fonts, 10-point tick/axis labels, 11-point bold strip headings, and 6.5 by 9 cm panels. Other manuscript figures preserve the original PDFs. Optional diagnostic plots from the reconstructed outputs go to a separate folder. The original figure scripts used their documented conventions; preserving them is a presentation choice, not a claim of pixel-identical regeneration from the consolidated code.

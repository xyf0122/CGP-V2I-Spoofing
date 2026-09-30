# Data dictionary

## trajectories.csv

7,151 rows from the attacked final intersection, 32 participants, nominal sampling interval 0.1 s. Original observation values are preserved; only participant keys and row order change.

| Column | Meaning / units |
| --- | --- |
| `participant_id` | Randomly reassigned participant key; shared with the survey and result files |
| `coord_2` | Simulator longitudinal coordinate in feet; decreases as the vehicle approaches the stop line |
| `speed` | Observed speed in mph |
| `accel_1` | Observed longitudinal acceleration in ft/s² |
| `time` | Seconds from initial RLCD presentation, starting at zero for each participant |

The coordinate is a simulated map position, not a participant's physical-world location. Internal position is `x = -coord_2`; `x_stop = -1074`; distance to the stop line is `coord_2 - 1074`. Multiplying mph by 1.4666666666666666 gives ft/s.

## geometry.json

The RLCD exposure anchor is 1414 ft, the stop-line anchor is 1074 ft, and the intersection boundary is 966 ft in `coord_2`. The empirical reconstruction uses zero additional safety buffer. The general mathematical framework supports positive buffers; that setting was not used for these reported reconstructions.

## survey_covariates.csv

32 rows, one per participant, with the same public key. No selected values are missing. Codes reproduce the archived analysis definitions.

| Column | Coding |
| --- | --- |
| `age` | Age in years; a source value above 1900 is treated as year of birth and converted using the original analysis year, 2022 |
| `gender` | 1 = male; 0 = female, matching the recorded responses |
| `yrs_drive` | Years of driving experience; one 41-year entry corrected to 10 years using that participant's explicit free-text experience response |
| `days_drive` | Reported driving days per week in the previous 12 months |
| `comfort_pre` | 1 very uncomfortable; 2 uncomfortable; 3 neutral; 4 comfortable; 5 very comfortable |
| `trust_pre` | 1 none at all; 2 a little; 3 a moderate amount; 4 a lot; 5 a great deal |
| `purchase_pre` | 1 very unlikely; 2 unlikely; 3 neither likely nor unlikely; 4 likely; 5 very likely |
| `abnormal` | Noticed abnormal vehicle behavior: 1 yes, 0 no |
| `cyber_belief` | Believed the vehicle was under cyberattack: 1 yes, 0 no |
| `opinion_change` | -2 a lot more negative; -1 a little more negative; 0 no change; 1 a little more positive; 2 a lot more positive |

The source survey remains unmodified. Selected pre/post responses were joined by the original survey record key before replacing it with the public participant key. The original join keys, birth dates, free text, IP addresses, collection metadata, and linkage file are excluded from this package.

## Results

`MAE` is mean absolute speed error in mph; `MSE` is mean squared speed error in mph². Errors are first computed within each participant's approach window, then summarized across the 32 participants without weighting by trajectory length.

`T_i` is the approach endpoint in seconds. `t2_hat` and `t2_reconstruction` are the same detected commitment time in seconds. `ttb0` is initial distance divided by initial speed in ft/s. `slack0 = 2*34*d0 - v0_ftps²`, in ft²/s². `a_pre`, `a_post`, and `da` are acceleration summaries in ft/s². `jerk_p95` is the 95th percentile of absolute observed finite-difference jerk, in ft/s³. `vmin_mph` is minimum observed speed within the evaluation window.

`primary_metrics_archived.csv` contains the original reference metrics with reassigned keys and the historical `ctrm` column suffix renamed `cgp`. Archived discussion correlations and Mantel outputs were stored at two-decimal precision; the new results retain full precision and documented analysis settings.

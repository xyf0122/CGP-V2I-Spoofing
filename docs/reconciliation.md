# Results reconciliation, 30 September 2026

The available research archive was used as the source. Original research input files were not edited.

| Issue | Evidence and resolution |
| --- | --- |
| Downsampling plots showed errors near 22 mph | `Location.txt` begins with `coord_2`. A script extracted all digits and selected the second number, 1414, as the stop line. The correct stop line is 1074. At the incorrect target, 10 Hz mean MAE/MSE reproduce as 22.116106 / 587.847287. Explicit named geometry fixes the parser error. |
| Numerical Table 6 versus downsampling figures | The archived Python detector and correct geometry reproduce every Table 6 value: 10 Hz mean MAE/MSE 2.281302 / 15.867964; 5 Hz 2.264211 / 15.637006. The table values remain unchanged; figures are regenerated. |
| Python, R plots, and appendix used different edge smoothing | The release uses the Python zero-padded five-sample mean throughout, because it reproduces the saved participant-level metrics and Tables 2–6. The appendix and empirical figure inputs are aligned with that convention. |
| SafeEnv win counts in prose | Saved metrics and reruns give 26/32 MAE wins and 25/32 MSE wins, replacing the prose's 29/32 and 28/32. Against ConstDecel, the corresponding counts are 28/32 and 27/32. |
| Pre/post commitment mean acceleration in discussion | Averages from the consistent evaluation window and detector are -1.584757 and -16.009641 ft/s², a difference of -14.424884. The prose is corrected to -1.58, -16.01, and -14.42. |
| Driving-experience data cleaning | One numeric value was 41 years, exceeding the participant's age. The explicit free-text experience response is 10 years. The public covariate file applies that documented correction; median 5.5 and range 1–16 reproduce the manuscript. |
| Approach-window and buffer description | Preprocessing now matches the implemented first-near-stop rule. The manuscript states that this empirical run uses zero additional safety buffer and constant 10 ft/s² planning deceleration. |
| Discussion plots and archived rounded outputs | Recomputed with the shared commitment times, corrected survey covariate, and explicit seeds. The original two-decimal reference CSVs remain in `reference/` as provenance, not validation targets for the corrected discussion pipeline. |
| Clipped IDM / Gipps | Original analysis remains pending recovery. No implementation, global parameter search, or participant-level results was found. Their reported values are not asserted to be reproduced. |

Tables 2 (three primary rows), 3, 4, 5, and 6 reproduce at the displayed precision. All 192 primary participant-level MAE/MSE values match the archived metrics within 1e-10. Only Figure 7c-d is replaced in the manuscript, using the original Figure 7a-b typography. The other 12 empirical figure PDFs retain the author's original presentation. Optional diagnostic redraws are kept separate; they are not replacements for manuscript figures.

The general mathematical framework and conceptual diagrams were not re-derived as part of this numerical reconciliation. The paper has not been compiled in this task.

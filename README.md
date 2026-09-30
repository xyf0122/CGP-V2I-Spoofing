# CGP reconstruction under V2I spoofing

Data and analysis code for **Modeling Driver Responses to V2I Spoofing: A Cognition-Gated Framework With Physical Constraints**.

This package reproduces the three primary models, constraint checks, acceleration distributions, ablations, downsampling analysis, and supporting discussion analyses for 32 participants. It includes 7,151 trajectory observations and ten selected survey covariates per participant.

**Release status:** initial research package, September 2026. The manuscript's clipped IDM and clipped Gipps comparisons are retained pending recovery of their original code, parameter search, and participant-level results. They are not reproduced by this package. See [release status](docs/release_status.md) before describing this as a complete reproduction of the paper.

[Repository](https://github.com/xyf0122/CGP-V2I-Spoofing)

## Run the analysis

Tested with Python 3.12.3 and R 4.4.3 with ggplot2 3.5.1. Install the tested Python dependencies into a virtual environment:

```text
python -m venv .venv
```

Activate that environment, then run these commands from this folder:

```text
python -m pip install -r requirements.txt
python scripts/run_all.py
python -m unittest discover -s tests
```

If Rscript is not on your PATH, supply its location:

```text
python scripts/run_all.py --rscript "C:/Program Files/R/R-4.4.3/bin/Rscript.exe"
```

The runner computes reconstruction results and supporting statistics, then regenerates Figure 7c-d in the original manuscript style. Install ggplot2 in R with `install.packages("ggplot2")` if needed; the tested version is 3.5.1. It uses paths relative to the repository, so the original research archive is not required. Generated results and Figure 7c-d are replaced. The other original manuscript figures are preserved. Optional diagnostic redraws from `python scripts/plot_figures.py` go into `figures/diagnostic_redraws/`. Inputs in `data/` and archived checks in `reference/` are read-only.

## Contents

| Folder | Contents |
| --- | --- |
| `data/` | Pseudonymized trajectories, selected survey covariates, and explicit simulator geometry |
| `src/` | One shared implementation of the verified CGP reconstruction and primary baselines |
| `scripts/` | Reproduction, statistical analysis, and plotting entry points |
| `results/` | Participant-level outputs, table summaries, PCA, regression, and Mantel results |
| `figures/` | Original empirical figures and corrected Figure 7c-d, with embedded fonts |
| `reference/` | Archived primary metrics and rounded discussion outputs for provenance |
| `tests/` | Regression checks against archived metrics and reported table values |
| `docs/` | Data dictionary, analysis conventions, discrepancy resolution, and release status |

Conceptual diagrams, manuscript drafts, cover letters, title pages, original notebooks, and the original survey workbook are outside this package.

## Verified headline results

| Model / resolution | Mean MAE (mph) | Mean MSE (mph²) |
| --- | ---: | ---: |
| ConstDecel, 10 Hz | 4.472980 | 30.295769 |
| SafeEnv, 10 Hz | 3.515779 | 23.057465 |
| CGP, 10 Hz | 2.281302 | 15.867964 |
| CGP, 5 Hz | 2.264211 | 15.637006 |

The 192 primary participant-level error values reproduce the archived CSV to an absolute tolerance of `1e-10`. CGP beats SafeEnv on MAE for **26/32** participants and MSE for **25/32**. The manuscript text has been corrected to these counts.

The downsampling plotting discrepancy came from parsing the digit in `coord_2` as a geometry value, shifting the stopping target from 1074 to 1414. Explicit named geometry values now prevent this error. [Reconciliation notes](docs/reconciliation.md) document the remaining corrections.

## Data handling and publication

Participants use randomly assigned `P001`–`P032` keys. The original ID mapping, IP addresses, birth-date/free-text fields, survey tracking IDs, timestamps, and collector metadata are excluded. The selected covariates preserve exact age and driving history for reproducibility; they remain participant-level research data. The original participant linkage and excluded survey records are not part of this release.

Code and software documentation are licensed under [MIT](LICENSE). Data, results, and figures are licensed under [CC BY 4.0](LICENSE-data.md). `CITATION.cff` supplies the citation metadata. The repository documents the pending IDM/Gipps evidence separately from the reproduced analyses.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A self-paced data analysis / ML learning curriculum built around SECOM manufacturing sensor data (`data/04_secom.csv`, 1567 rows × 590 sensor columns + `result`) and a bottling-line dataset (`data/day01_bottling.csv`). There is no application code, package manifest, build system, or test suite — the deliverables are Jupyter notebooks (`.ipynb`) organized by day and lab, written and executed incrementally as teaching exercises. Notebook prose and variable/function names are in Korean, matching the pedagogical style — keep that convention when editing existing notebooks.

## Environment

- Python is not reliably on `PATH` as `python` (it may resolve to the Windows Store alias stub instead of the real interpreter). Call the interpreter by its full path:
  `C:\Users\정유진\AppData\Local\Programs\Python\Python314\python.exe`
- Installed packages: `pandas`, `matplotlib`, `scikit-learn`, `nbconvert`, `ipykernel` (install additional ones with `<python> -m pip install <package>`).
- Not a git repository — there is no version control in this directory.

## Running a notebook

There is no live/attached Jupyter kernel in this environment. To actually execute a notebook's cells and populate real outputs, run it headlessly with `nbconvert`, from the repo root (`nbconvert` uses the notebook's own directory as the execution `cwd`, so relative paths inside cells resolve relative to the notebook file, not the repo root):

```
<python> -m nbconvert --to notebook --execute --inplace "day0N\labXX_name\labXX_name.ipynb"
```

Avoid piping this command's stderr with `2>&1` in PowerShell — it wraps normal nbconvert progress/warning lines in `NativeCommandError` even when the run succeeds, which reads as a false failure. Let stderr print naturally instead.

## Architecture: the lab pipeline

Each `dayNN/labXX_<name>/` folder holds one notebook plus a `results/` subfolder for that lab's saved outputs (PNG charts, cleaned CSVs). Labs build on each other in sequence, each reading the previous lab's saved output rather than the raw data directly once cleaning has started:

- `day02/lab04_control-chart` — control-chart exploration on a single raw sensor column from `data/04_secom.csv`.
- `day02/lab05_sensor-diagnosis` — builds a per-column diagnostic table (missing %, unique count, std, min/max) across all 590 sensor columns to decide which are usable.
- `day02/lab06_clean-dataset` — applies the selection criteria from lab05, drops near-duplicate/correlated sensor columns, and writes the cleaned feature table to `day02/lab06_clean-dataset/results/secom_clean.csv` (and a `secom_clean_b.csv` variant). This is the canonical cleaned dataset consumed by everything downstream.
- `day03/lab07_train-test-split` — loads `secom_clean.csv`, median-imputes remaining gaps, encodes `result` (양품/불량) into a numeric `불량여부` target, and produces a stratified train/test split.
- `day03/lab08_baseline-model` — reproduces the lab07 split from scratch and compares a zero-effort baseline (always predict 양품) against a scaled logistic-regression classifier.

When adding a new lab, follow this pattern: read the prior lab's `results/` output (relative path from the new notebook's own folder), do the work in cells, and if the lab produces a reusable artifact, save it under that lab's own `results/` folder.

## Known editor quirk

When a notebook is open in the VS Code editor while it's also being edited/executed from the CLI (via `NotebookEdit` + `nbconvert`), VS Code's own autosave can periodically overwrite the file on disk with a stale in-memory copy, silently dropping cells that were just added and executed. After any edit+execute cycle, re-read the notebook file to confirm the new cell (and its output) actually persisted before reporting results, and re-add it if it didn't.

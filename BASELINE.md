# First milestone: reproduce the starter

## 1. Resolve prerequisites

- Team repo is https://github.com/althafurahman/A1 and has been cloned. Preserve its existing files/history.
- Import or integrate the pinned upstream starter without replacing existing team work. Record upstream commit and any differences.
- Confirm exact Qwen3.8-27B Tinker API identifier. User clarified Claude Code/Codex are development tools, not solver models.
- User accepts invitation and creates one shared Tinker project. Configure TINKER_API_KEY privately; never put its value in documentation.
- Check Python >=3.11, uv, Docker runtime and LibreOffice. A Docker executable alone does not establish that its daemon is running.
- Ask for judge runtime/resource limits and any model request limits before sizing full runs.

## 2. Verify evaluation before inference

From the imported research directory:

```sh
uv sync --extra tinker
uv run data/download.py
uv run evaluate.py --oracle
```

The oracle check compares supplied golden files against themselves and should report 1.0. It checks loading/comparison, not model ability; this mode bypasses recalculation. Separately verify LibreOffice recalculation works before the full scored run.

Read dependency/install commands before executing and use normal approval mechanisms where needed. Do not run the README's alternative-model examples.

## 3. Smoke test the unchanged baseline

Once the exact model is confirmed, set A1_ALLOWED_MODEL_ID to that verified identifier. Do not use a guessed example.

```sh
uv run baseline/tinker_predict.py --out-dir submissions/baseline-smoke-001 --base-model "$A1_ALLOWED_MODEL_ID" --ids 13-1,51-12
uv run evaluate.py --predictions submissions/baseline-smoke-001/predictions.jsonl --out submissions/baseline-smoke-001/results.json
```

Verify workbook creation, traces, model identity, usage/error records and successful scoring. A subset score is not the full baseline.

## 4. Reproduce all 400

Use a fresh output directory. The starter clears outputs/traces on startup, so do not reuse an evidence directory.

```sh
uv run baseline/tinker_predict.py --out-dir submissions/baseline-full-001 --base-model "$A1_ALLOWED_MODEL_ID"
uv run evaluate.py --predictions submissions/baseline-full-001/predictions.jsonl --all --out submissions/baseline-full-001/results.json
```

Record upstream/team commits, exact model, parameters, dependency versions, elapsed time, token/credit usage if available, errors and summary. Capture complete stdout/stderr in addition to starter logging to satisfy final run.log requirements.

59% is a reference, not an assertion. If our score differs, investigate model/configuration, data, transport failures and evaluation before claiming a reasoning improvement. Do not tune just to reproduce a number.

## 5. Acceptance and next experiment

- All 400 task records and output files accounted for; errors identified honestly.
- Official results saved; items=400; recalculation enabled.
- No alternative models or golden answers used in inference.
- Baseline evidence preserved and reproducible from documented commands.
- Categorise failures from actual traces before proposing fixes.

Only then test one change at a time: relevant workbook access, programmatic computation, or bounded repair. Keep a development subset and untouched validation subset to reduce overfitting. Fine-tuning requires a justified failure pattern and clarified training-data rules.

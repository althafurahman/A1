# Submission: A1

## Team

- Team name: A1
- Members, one GitHub handle per line:
  - althafurahman
  - mboosiri
- Repo URL: https://github.com/althafurahman/A1

## What we built and why

SpreadsheetBench tasks are graded cell-by-cell on values, and the organiser's one-shot
baseline (a 120x30 text preview of the workbook, model types out every answer cell as
JSON) fails in ways that have little to do with reasoning: dates come back as text, rows
past 120 are invisible, and large answer ranges exhaust the thinking budget before any
JSON appears. We built a code-executing agent around the fixed model, Qwen3.8-27B via
Tinker at temperature 0. The model receives an answer-region-aware serialisation (head,
tail and answer rows of every sheet, plus a formula overlay) and writes one Python
script that opens the real workbook with openpyxl, computes the result, and writes plain
values into the graded region. The script runs in a scratch directory inside the
container; failures feed stderr back for a bounded repair loop. A produced output then
passes mechanical hygiene checks (no formula strings, no padded text) and an LLM
verification pass that sees the answer region before and after the script, which
catches row-shifted and partially filled regions. Only if the code path produces nothing
does a direct JSON-answer fallback run. Developed one change at a time on a 16-task
stratified dev subset: unchanged baseline 10/16; harness 14/16, then 15/16 after the
whitespace-hygiene and before/after-verifier fixes. On the full 400: pass_rate 0.870,
cell_accuracy 0.9729. Limits, honestly: 2/400 produced no answer (the model exhausts its
budget thinking about 5000-row ranges before emitting code); sampling wobbles ±1–2 tasks
even at temperature 0; the run executed in four segments after two external process
kills and a mid-run 64k-context fix — errored ids were re-run with the fixed harness,
completed answers were never re-rolled (chronology in MEMORY.md). No fine-tuning.

## Models

- `Qwen/Qwen3.8-27B` (base model, no fine-tune), sampled through the Tinker API with the
  tinker-cookbook Qwen3.8 renderer (thinking enabled, default reasoning effort),
  temperature 0, max_tokens 24576 clamped to the 64k context. Every call in the pipeline
  (code generation, repair, verification, direct fallback) uses this model.

## Scores on the 400

Produced by the shipped evaluator (`results.json` in the repo root):

```sh
uv run evaluate.py --predictions predictions.jsonl --all --out results.json
```

```json
{"items": 400, "graded": 400, "missing": 0, "errors": 0, "pass_rate": 0.87, "cell_accuracy": 0.9729, "pass_rate_cell_level": 0.9091, "pass_rate_sheet_level": 0.784}
```

## Your run on the 400

- `predictions.jsonl`: repo root
- `outputs/`: repo root, one workbook per task
- `traces/`: repo root, one `<id>.jsonl` per task, one line per model call, plus tool
  lines (`tool`, `tool_input`, `tool_output`) for each script execution. Prompt fields
  are truncated to 20,000 characters and tool output to 8,000 characters.
- `run.log`: repo root (four segments, concatenated; chronology in MEMORY.md)

## Code

The pipeline executes model-written Python, so it runs in Docker:

```sh
docker build -t a1 .
docker run --rm -e TINKER_API_KEY -e TINKER_PROJECT_ID -v <dataset dir>:/data:ro -v <empty dir>:/out a1
```

Environment variables: `TINKER_API_KEY` (Tinker API key), `TINKER_PROJECT_ID` (the
Tinker project the key belongs to). The model id is fixed in `a1/run.py` and
`a1/tinker_llm.py`.

## Things to look at

- `research/submissions/dev16-baseline-001/results.json` — unchanged organiser baseline on the dev16 subset (10/16), the reference the harness is measured against.
- `experiments/dev16-a1-001/results.json`, `experiments/dev16-a1-002/results.json` — the harness on the same 16 tasks (14/16, then 15/16 after the fixes below).
- `experiments/fix-check-001/`, `experiments/fix-check-002/` — single-task checks of the whitespace hygiene rule and the before/after verifier (156-14 and 230-16 go from near-miss to pass).
- `experiments/dev16.ids` — the stratified dev subset (4 tasks per cell/sheet x small/large answer range bucket).
- `a1/harness.py` — the pipeline: prompts, hygiene checks, verifier, repair loop.
- `a1/serialize.py` — answer-region-aware serialisation; why the one-shot baseline is blind on workbooks larger than 120 rows.
- `MEMORY.md` — dated log of every run, failure category, cost and decision, including the full-400 chronology.
- `experiments/ext40/` and `experiments/ext40-base-001/results.json` — generalisation check on 40 unseen tasks from the original SpreadsheetBench pool (not in the Verified 400; built by `scripts/build_ext40.py`, caveat in the README): 26/40 pass vs 87% on the 400; failure analysis in MEMORY.md.

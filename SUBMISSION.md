# Submission: A1

## Team

- Team name: A1
- Members, one GitHub handle per line:
  - (fill in)
  - (fill in)
- Repo URL: https://github.com/althafurahman/A1

## What we built and why

SpreadsheetBench tasks are graded cell-by-cell on values, and the organiser's one-shot baseline (a 120x30 text preview of the workbook, model types out every answer cell as JSON) fails in ways that have nothing to do with reasoning: dates come back as text, rows past 120 are invisible, and large answer ranges exhaust the thinking budget before any JSON appears. On our 16-task stratified dev subset the unchanged baseline scored 10/16 and 70% of its model time went to the six failures. We therefore built a code-executing agent around the fixed model, Qwen3.8-27B via Tinker at temperature 0. The model receives an answer-region-aware serialisation (head, tail and answer rows of every sheet, plus a formula overlay) and writes one Python script that opens the real workbook with openpyxl, computes the result, and writes plain values into the graded region. The script runs in a scratch directory inside the container; failures feed stderr back for a bounded repair loop (two repairs). A produced output then passes mechanical hygiene checks (no formula strings, no padded text) and an LLM verification pass that sees the answer region before and after the script, which catches row-shifted and partially filled regions. Only if the code path produces nothing does a direct JSON-answer fallback run. On dev16 this reached 15/16 (cell accuracy 0.971) against 10/16 for the baseline, with the remaining miss a sampling wobble on a weighted-average task that passes in other runs. What did not work: the first serialisation budget overflowed the 64k context on very large workbooks; we now shrink the serialisation and clamp max_tokens on overflow. No fine-tuning was used.

## Models

- `Qwen/Qwen3.8-27B` (base model, no fine-tune), sampled through the Tinker API with the tinker-cookbook Qwen3.8 renderer (thinking enabled, default reasoning effort), temperature 0, max_tokens 24576 clamped to the 64k context. Every call in the pipeline (code generation, repair, verification, direct fallback) uses this model.

## Scores on the 400

Produced by the shipped evaluator:

```sh
uv run evaluate.py --predictions <your predictions.jsonl> --all --out results.json
```

```json
(paste the summary block of results.json here after the full run)
```

## Your run on the 400

- `predictions.jsonl`: repo root
- `outputs/`: repo root, one workbook per task
- `traces/`: repo root, one `<id>.jsonl` per task, one line per model call, plus tool lines (`tool`, `tool_input`, `tool_output`) for each script execution. Prompt fields are truncated to 20,000 characters and tool output to 8,000 characters.
- `run.log`: repo root

## Code

The pipeline executes model-written Python, so it runs in Docker:

```sh
docker build -t a1 .
docker run --rm -e TINKER_API_KEY -e TINKER_PROJECT_ID -v <dataset dir>:/data:ro -v <empty dir>:/out a1
```

Environment variables: `TINKER_API_KEY` (Tinker API key), `TINKER_PROJECT_ID` (the Tinker project the key belongs to). The model id is fixed in `a1/run.py` and `a1/tinker_llm.py`.

## Things to look at

- `research/submissions/dev16-baseline-001/results.json` — unchanged organiser baseline on the dev16 subset (10/16), the reference the harness is measured against.
- `experiments/dev16-a1-001/results.json`, `experiments/dev16-a1-002/results.json` — the harness on the same 16 tasks (14/16, then 15/16 after the fixes below).
- `experiments/fix-check-001/`, `experiments/fix-check-002/` — single-task checks of the whitespace hygiene rule and the before/after verifier (156-14 and 230-16 go from near-miss to pass).
- `experiments/dev16.ids` — the stratified dev subset (4 tasks per cell/sheet x small/large answer range bucket).
- `a1/serialize.py` — answer-region-aware serialisation; why the one-shot baseline is blind on workbooks larger than 120 rows.
- `MEMORY.md` — dated log of every run, failure category and decision.

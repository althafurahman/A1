# Submission: A1

## Team

- Team name: A1
- Members, one GitHub handle per line:
  - althafurahman
  - mboosiri
- Repo URL: https://github.com/althafurahman/A1

## What we built and why

SpreadsheetBench only credits a task when every answer cell is right after recalculation, so the real problem is reliability, not average cleverness. The organisers' baseline shows the model a 120-row text dump and asks it to type every answer cell as JSON. Reading its traces on a 16-task dev subset (10/16 pass) showed the misses were mechanical: dates written as text, rows past 120 invisible, thinking budgets spent enumerating 190-cell ranges, answers shifted by a row. We built a code-executing agent around the fixed model, Qwen3.8-27B via Tinker at temperature 0. The model sees an answer-region-aware view of every sheet (head, tail, answer rows, formulas next to their cached values) and writes one Python script that opens the real workbook with openpyxl and writes plain, correctly typed values into the graded region. The script runs in a scratch directory; errors go back for a bounded repair loop. Two checks follow: mechanical hygiene (no formula strings, no padded text) and a verifier that sees the answer region before and after the script, which is what catches row shifts and half-filled regions. A direct JSON answer runs only if no script ever produced a file. Every task always yields a workbook and one trace line per model call. Each change was driven by one failed task and verified on it: 10/16 became 14/16, then 15/16. Full 400: pass_rate 0.870, cell_accuracy 0.9729. What did not work: a LoRA fine-tune on the model's own verified scripts ran 14x cheaper but lost the reasoning (52/78 vs 68/78 held out), so it is reported, not used. Known limits: 2/400 unanswered on 5,000-row ranges, a one or two task sampling wobble at temperature 0, and a run completed in four segments (chronology in LABNOTES.md).

## What stands out, and why the numbers can be trusted

This system is built for the job a spreadsheet user actually has: hand over a file and a request, get the finished file back, every time, with a record of how it was done.

- **Reliability is the contract.** Every one of the 400 tasks produced an output workbook, a status line and a full trace, including the two the model could not solve. Failures are declared, not hidden.
- **The model edits the real file.** It never reads a truncated picture of the sheet and never re-types data. It writes a script that reads the actual cells, so large ranges and long sheets cost nothing extra and values keep their types (real dates, real numbers).
- **A verifier that sees before and after.** Most checks look only at the output. Showing the original region beside the written one is what turns "looks plausible" into "the right cells changed and nothing else did".
- **Evidence-first development.** Each change came from one named failure in a trace and was confirmed on that task before the full run. Runs are committed with their results files; LABNOTES.md links every decision to one.
- **We tested where we had not tuned.** 40 tasks from outside the Verified 400 score 26/40. We report that gap and its caveats rather than only the number that flatters us.
- **Nothing is hidden from the judges' run.** The pipeline never reads golden files; traces hold the model's own reasoning and scripts. The container was rebuilt from a clean checkout on submission morning and run under the exact judge command.

## Models

- `Qwen/Qwen3.8-27B` (base model, no fine-tune), sampled through the Tinker API with the tinker-cookbook Qwen3.8 renderer (thinking enabled, default reasoning effort), temperature 0, max_tokens 24576 clamped to the 64k context. Every call in the pipeline (code generation, repair, verification, direct fallback) uses this model.

## Fine-tuning experiment (not used at inference)

We asked whether the expertise could move from the scaffolding into the weights, as in the Tinker text-to-SQL case study. Reinforcement learning was ruled out by arithmetic: one training step would need about 8M tokens of sampling. Instead:

- LoRA rank 32, lr 2e-4, batch 32, 2 epochs (16 steps, 1.34M tokens, about a minute on Tinker). Sampler checkpoint, TTL cleared: `tinker://17741918-b3a7-5ae6-bf92-9556e1033720:train:0/sampler_weights/final`.
- Training data: 258 prompt-to-script pairs from our own 400 run (`experiments/sft-001/train.jsonl`, ids in `train_ids.txt`), chosen because the shipped evaluator marked them as passing. The 400 golden files therefore influenced example selection; 78 stratified tasks (`experiments/heldout78.ids`) were never trained on and are the only numbers we report.
- Result on the held-out 78: 52/78 pass against 68/78 for the base model, at 1,313 against 18,104 output tokens per task. The fine-tune keeps the coding style and speed but loses the reasoning that decides what to compute, and the shared verifier weakens with it. Speed and accuracy turned out to be separable, which points at the cascade in future work.

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
- `traces/`: repo root, one `<id>.jsonl` per task, one line per model call, plus tool lines (`tool`, `tool_input`, `tool_output`) for each script execution. Prompt fields are truncated to 20,000 characters and tool output to 8,000 characters.
- `run.log`: repo root (four segments, concatenated; chronology in LABNOTES.md)

## Code

The code that produced the run is in the repo. One change landed after the run: commit 46fb92d widens the retry token budget from 24,576 to 45,000 when a reply is cut off mid-reasoning (a1/harness.py). The 400-task run above was produced at commit 6a77606 without it, and the two tasks that errored there still fail with it.

The pipeline executes model-written Python, so it runs in Docker:

```sh
docker build -t a1 .
docker run --rm -e TINKER_API_KEY -v <dataset dir>:/data:ro -v <empty dir>:/out a1
```

Environment variables: `TINKER_API_KEY` only. The team's Tinker project id and the model id are fixed in code (`a1/tinker_llm.py`, `a1/run.py`), so the container runs exactly the way we ran it; setting `TINKER_PROJECT_ID` explicitly overrides the default.

## Future work

- A cascade: the fine-tuned model first for its 14x token efficiency, the base model as verifier and fallback.
- The `prompt-fixes` branch (copy-verbatim rules for moved values, whitespace and type rules only for computed ones) recovers 19 of the 52 failures on the 400 but needs two full runs to beat sampling variance, so it is not merged.
- An exploration turn before writing code for lookup-style tasks, the largest block of real failures on the unseen 40.
- A formula mode with LibreOffice recalculation inside the container, for tasks whose goldens keep formula-produced text formats.

## Things to look at

- `research/submissions/dev16-baseline-001/results.json`: the unchanged organiser baseline on the dev16 subset (10/16), the reference the harness is measured against.
- `experiments/dev16-a1-001/results.json`, `experiments/dev16-a1-002/results.json`: the harness on the same 16 tasks (14/16, then 15/16 after the fixes below).
- `experiments/fix-check-001/`, `experiments/fix-check-002/`: single-task checks of the whitespace hygiene rule and the before/after verifier (156-14 and 230-16 go from near-miss to pass).
- `experiments/dev16.ids`: the stratified dev subset (4 tasks per cell/sheet x small/large answer range bucket).
- `a1/harness.py`: the pipeline: prompts, hygiene checks, verifier, repair loop.
- `a1/serialize.py`: answer-region-aware serialisation; why the one-shot baseline is blind on workbooks larger than 120 rows.
- `experiments/sft-001/` and `experiments/heldout78-sft-001/`: the LoRA experiment: training set, config, metrics, checkpoint path, and the held-out evaluation with traces.
- `experiments/ext40/` and `experiments/ext40-base-001/results.json`: generalisation check on 40 unseen tasks from the original SpreadsheetBench pool (not in the Verified 400; built by `scripts/build_ext40.py`, caveat in the README): 26/40 pass; failure analysis in LABNOTES.md.
- `LABNOTES.md`: dated log of every run, failure category, cost and decision, including the full-400 chronology.

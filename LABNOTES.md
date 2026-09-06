# A1 lab notebook

Dated log of every experiment, run, failure category and decision. Facts only, in the
order they happened. Updated 2026-09-06 09:15 (final status at the bottom).

## Setup and baseline reproduction (2026-09-05 afternoon)

- Two-person team: one owns product/architecture/data/ML, one senior full-stack developer.
- Starter imported: `research/` copied byte-identical from https://github.com/ylookup/encode-hackathon commit 37d9016264762a25cae49e077cd0893055bd9093 (verified with diff -r). See `research/UPSTREAM.md`.
- `.gitignore` rule `data/` narrowed to `/data/` so `research/data/download.py` is tracked; the downloaded dataset and tarball stay ignored.
- Environment verified (macOS, Apple Silicon): uv 0.10.10; venv Python 3.13.12, tinker 0.27.1, tinker-cookbook 0.5.7, openpyxl 3.1.5 from the starter lock. Dataset downloaded, checksum OK (400 tasks). `evaluate.py --oracle` → pass_rate 1.0 on 400 (grader plumbing correct; says nothing about model ability). LibreOffice 26.8.0.3 recalculation verified on a formula with no cached value. Docker Desktop 29.1.2 running.
- Model identifier confirmed on the Tinker models page: `Qwen/Qwen3.8-27B` (~$1.86/M prefill, $5.60/M sample; tinker-cookbook renderer `qwen3_8_xhigh_reasoning`).
- Tinker access: first attempt without a project id failed with `400 This project is read-only` (org default project); fixed by setting TINKER_PROJECT_ID. Log in `research/submissions/baseline-smoke-001/console.log`.
- Baseline smoke tests (unchanged starter `baseline/tinker_predict.py`, temperature 0):
  - `research/submissions/baseline-smoke-002/` (default `--max-tokens 8192`): both tasks hit exactly 8192 output tokens still inside the think block, no JSON parsed, pass_rate 0.0. ~103 s per task.
  - `research/submissions/baseline-smoke-003/` (`--max-tokens 24576`): both parsed. 51-12 PASS (5,271 out tokens, 63 s). 13-1 101/120 cells (12,814 out tokens, 154 s).
  - 13-1's 19 misses are all dates: the model returned strings like `2024-02-03 00:00:00`, the starter writes them as text, the golden has real datetimes. Failure category: value typing at write time, not reasoning.
  - Same task gave 8192+ tokens in one run and 5,271 in another: sampling varies even at temperature 0.
  - Throughput ~80 output tokens/s per request.
- Dev subset: `experiments/dev16.ids` = 16 tasks, 4 per bucket (cell/sheet × small/large answer range), seeded, excludes smoke ids.
- `research/submissions/dev16-baseline-001/` (unchanged starter, `--max-tokens 24576 --concurrency 8`): pass_rate 0.625 (10/16), cell_accuracy 0.516, cell-level 7/8, sheet-level 3/8. 2 truncated at the cap. 1,219 s, 144k output tokens, ~$0.85.
  - Aggregate ~118 tok/s at concurrency 8 vs ~80 tok/s single — read at the time as a project-level rate limit (later disproved, see the full-400 chronology).
  - Failure categories from traces (6 fails): truncation ×2 (183-8 reasoning never converged; 57232 ran out of tokens emitting a 190-cell JSON); row-shift/manipulation ×2 (230-16 shifted one row, 156-14 wrong rows deleted); misread task ×1 (263-1 wrote category names instead of totals); near miss ×1 (203-15 missed a header, 38/39). Plus 13-1's dates-as-text.
  - Interpretation: sheet-level tasks with many cells are where text-dump-and-enumerate fails — the model must reason about and re-emit every cell. Cell-level tasks are already strong.

## Decisions (standing)

- First milestone was baseline reproduction, not optimisation; one change at a time thereafter.
- Starter code and official evaluator reused unchanged; only the confirmed model is ever called.
- Coding assistants are development tools only, never solver models.
- Do not re-run paid experiments without a team decision; never re-roll completed answers.

## Harness results (2026-09-05 evening)

The code-executing agent proposed in the root README, implemented in `a1/` and measured.
Pipeline per task: model writes an openpyxl script (INIT/OUT contract, values only) → script runs
in a scratch dir → mechanical hygiene checks (formula strings, stray whitespace) → verification
call shown the answer region BEFORE (init) and AFTER (output) → bounded repair loop (2) → direct
JSON-answer fallback only if the code path produced no output at all. Model access: Tinker,
`Qwen/Qwen3.8-27B`, temperature 0, max-tokens 24576.

- `experiments/smoke-a1-001/`: 13-1 and 51-12 both PASS (baseline: 13-1 failed on dates-as-text).
- `experiments/dev16-a1-001/` (concurrency 6): pass_rate 0.875 (14/16), cell_accuracy 0.9865,
  cell-level 8/8, sheet-level 6/8. 34 model calls (16 code, 17 verify, 1 repair), 207k output
  tokens, ~24 min, ~$1.29. Both failures near-misses: 230-16 trailing whitespace in text values
  (7/12), 156-14 two cells left empty (154/156).
- Fixes, one at a time: whitespace hygiene check + strip rule; verifier surfaces EMPTY cells and
  compares the region before/after (row-shift detection); produced outputs are kept over the
  fallback; missing answer sheets are created by name, never written to the active sheet.
- `experiments/fix-check-001/`: 156-14 PASS 156/156. 230-16 regressed to 2/12 via a differently
  sampled script (row shift; sampling varies at temp 0) — motivated the before/after verifier.
- `experiments/fix-check-002/`: 230-16 PASS 12/12, first attempt, no repairs.
- `experiments/dev16-a1-002/` (final config confirmation): pass_rate 0.9375 (15/16),
  cell_accuracy 0.971, cell-level 8/8, sheet-level 7/8. 32 calls, 248k output tokens, ~$1.52.
  Sole failure 183-8 — it passed in dev16-a1-001; temperature-0 sampling wobble, same as the
  baseline shows. Every dev16 task passed with the final config in at least one run.
- Pre-run review of the whole branch surfaced 15 verified findings (forbidden-model defaults in
  starter docs, doc/env bugs, evaluator quirks such as noon-datetime rounding and the
  cell_accuracy denominator); doc-level items were fixed or the files later removed in cleanup.

## Docker and submission prep (2026-09-06 01:00–01:35)

- Docker image built and run exactly per the judge contract (`/data` read-only, empty `/out`,
  keys via env): tasks 51-12 and 79-7 both PASS under the shipped evaluator; traces carry every
  required field plus phase/tool lines; no `golden` string in prompts or traces.
- Dockerfile hardened without changing pipeline behaviour: CPU-only torch index (image
  9.75 GB → 2.06 GB) and the Qwen3.8 tokenizer baked at build time so start-up does not depend
  on Hugging Face.
- Cost profile in-container: a 1-cell task spent 17,929 output tokens (366 s) in the code call at
  the default (xhigh) reasoning effort; the verify call 1,248. Reasoning effort is the main time
  lever if a rerun is ever needed.
- `scripts/finalize.sh <run dir>`: scores with `--all`, copies artifacts to the repo root, greps
  traces for `golden`. `scripts/analyse_run.py <run dir>`: per-task calls/tokens/time and
  failure buckets.

## Full-400 run (night of 2026-09-05→06) — SUBMITTED ARTIFACTS

Final score, shipped evaluator, `--all`, recalculation on: **pass_rate 0.870, cell_accuracy
0.9729, cell-level 0.9091, sheet-level 0.784** (items 400, missing 0). Artifacts at repo root
(`predictions.jsonl`, `outputs/`, `traces/`, `run.log`, `results.json`).

Chronology (disclosed in SUBMISSION.md): the run executed in four segments, merged last-wins
on non-ok status; completed answers were never re-rolled.
- `full-400-001` (00:39, concurrency 16): killed externally at 253/400. Observed 470→820 tok/s
  aggregate — the assumed ~140 tok/s project cap was wrong; throughput scales with concurrency
  and off-peak hours. 17 errors, mostly context-window overflows on giant workbooks.
- Mid-run fix (commit a76d3a5; solver prompts unchanged for normal tasks): Tinker serves the
  model with a 64k context, not 1M — clamp max_tokens to fit, shrink serialization on overflow
  (120k→45k→16k chars), route no-code-block replies through the repair nudge.
- `full-400-002` (concurrency 10): killed at 10 tasks. Both kills took locally supervised
  background processes only — the machine never slept; the cause was the local task supervisor,
  not OOM. Lesson: long runs must be nohup-detached.
- `full-400-003` (detached, concurrency 10): survived but slow (~250 tok/s); stopped by us.
- `full-400-004` (detached, concurrency 16): 144 tasks, no interruption, finished 03:50. The
  former overflow errors passed with the fix (80-42, 209-30, 455-35, 41-47, ...).
- Remaining failures: 2/400 with no answer (118-50, 42216 — the model exhausts its budget
  thinking about 5000-row ranges before emitting code; init copies stand in, status honest).
- Night's spend: ~7.6M output tokens, ≈$45.

## LoRA SFT experiment (branch `lora-sft`, 2026-09-06 04:40–06:00)

Goal: a model-side improvement feasible in the remaining hours (put task expertise into weights,
cut test-time scaffolding). RL was ruled out by arithmetic (one GRPO step at ~15k thinking tokens
per sample is ~8M tokens, ~18 h at the shared rate). Chosen: rejection-sampling SFT on the
harness's own verified outputs, trained to emit the script with an empty think block.

- Data: `scripts/build_sft.py` rebuilt the exact inference prompt for every task that PASSED in
  the 400 run and is not in `experiments/heldout78.ids` (78 stratified held-out ids incl. dev16);
  target = the reply that produced the last successful script. 258 examples, 665k tokens (median
  1,852), 17 skipped as too long, 5 without a usable reply, 10 samples hand-audited (all read the
  workbook, none hard-code answers). Golden files were used only to SELECT examples; disclosed.
- Training: `scripts/train_sft.sh sft-001` = cookbook `chat_sl` recipe, LoRA rank 32, lr 2e-4,
  batch 32, 2 epochs = 16 steps, 1.34M tokens, ~4 s/step, final train NLL 0.205 (from 0.228).
  Checkpoint (TTL cleared): `tinker://17741918-b3a7-5ae6-bf92-9556e1033720:train:0/sampler_weights/final`. ~$6.
- Evaluation `experiments/heldout78-sft-001/` (same harness, `--model-path`, ~10 min, ~$3.5)
  vs the base model's own results on the same 78 ids:

  | | base model | fine-tuned |
  |---|---|---|
  | pass | 68/78 | 52/78 |
  | cell-level / sheet-level | 35/40, 33/38 | 27/40, 25/38 |
  | cell_accuracy | ~0.97 | 0.986 |
  | mean output tokens/task | 18,104 | 1,313 |
  | mean model seconds/task | 335 | 50 |
  | mean model calls/task | 2.28 | 3.47 |

- Reading: the fine-tune keeps the code style and speed (14× fewer tokens, 7× faster) but loses
  the reasoning that decides *what* to compute: failures are interpretation errors, not
  truncation or plumbing; 20 of 26 failures are partial. Because verify/repair use the same
  no-think model, the verifier also weakened: it passed 12 of the 26 failing outputs, and 9
  tasks looped through repair without converging. Won 2 tasks the base missed, lost 18.
- Decision per the pre-agreed gate (within 2 tasks of base): NOT used for the submission.
  Natural follow-ups (not attempted, no time): cascade (fine-tuned first, base on verifier
  reject), keep the base model for the verify phase, or SFT targets with a short thinking trace.

## Failure taxonomy of the 52 fails (2026-09-06 morning)

20 near-miss (≥90% of cells right), 20 partial, 12 zero-correct. Notable honest findings:
- The strip-whitespace hygiene rule cuts both ways: 290-27 expected 'GG ' (trailing space kept
  in golden), 341-40 expected ' Sales' (leading space) — we strip and lose those cells, while
  the same rule won 230-16 on dev16. Net effect unknowable without golden access; disclosed.
- 269-43: the golden stores dates as TEXT ('2022/01/26'); our real-datetime rule loses there.
  The reverse of the baseline's dates-as-text failure — some goldens genuinely want text.
- 41-47: 6395/6403 cells right, missing 8 'TOTAL' label rows.
- 118-50, 42216 (the 2 no-answer errors): the model exhausts 24,576 tokens mid-think before
  emitting code. Fix attempted: the no-code-block retry now escalates max_tokens to 45k
  (context clamp still protects the ceiling). Errored-id re-run in `experiments/error-retry-001/`
  — same disclosed policy as the night segments. OUTCOME: both still fail at 45k (118-50 never
  emits code; 42216's script arrives truncated mid-line) — a genuine capability edge of the 27B
  on these two tasks, not a budget problem. Submitted artifacts unchanged; the escalation fix
  stays in the code where it can help the judges' holdout run. Note: 118-50's graded region is
  ~10k cells of which only 22 differ from the init workbook — one reason cell_accuracy (0.9729)
  sits far above pass_rate.

## ext40 generalisation set (branch `ext40-data`, 2026-09-06 03:00)

- `experiments/ext40/`: 40 unseen tasks from the original SpreadsheetBench 912
  (HF KAKA22/SpreadsheetBench, CC BY-SA 4.0) that are not in the Verified 400. Built by
  `scripts/build_ext40.py` (seed 1): 512 candidates → 353 eligible after dropping empty
  instructions, formatting/volatile tasks, unchanged answer ranges, missing answer sheets,
  >2000-cell ranges and one unloadable file; 10 per bucket (cell/sheet × ≤15/>15 cells).
  Renamed to the Verified layout; oracle 1.0 on 40/40.
- Caveat: unverified leftover pool, so treat ext40 scores as relative between configs.
- `experiments/ext40-base-001` (submitted harness, concurrency 16, 04:43–05:09, ~$6.5, mean 25k
  output tokens/task): pass_rate 0.65 (26/40), cell_accuracy 0.863, cell-level 14/20,
  sheet-level 12/20. Versus 0.87 / 0.909 / 0.784 on the Verified 400. Of the 14 fails: 2 are the
  whitespace-strip rule, 1 case-sensitivity, 1 harness error (no code block), ~2–3 look like
  golden quirks of the unverified pool, the rest genuine wrong values, mostly cell-level formula
  tasks (lookups, conditional sums). Honest read: ~12–15 points of real generalisation gap
  beyond self-inflicted rules and label noise.
- Same self-inflicted pattern on the 400: of 52 fails, 7 whitespace-strip, 4 text-date-converted,
  18 empty header/label cells. Follow-up prompt fix drafted: values copied or moved from existing
  cells must be copied verbatim (type and whitespace); typing/strip rules apply only to newly
  computed values.

## Final status (2026-09-06 09:15)

- Submission = `main`. Root `predictions.jsonl`, `outputs/`, `traces/`, `run.log`,
  `results.json` are the full-400 run: pass_rate 0.87 (348/400), cell_accuracy 0.9729,
  cell-level 0.9091, sheet-level 0.784. Model `Qwen/Qwen3.8-27B` via Tinker, temperature 0,
  no fine-tune at inference. Docker image verified per the judge contract (2.06 GB, tokenizer
  baked in).
- One harness change after the run (46fb92d, wider retry token budget) is declared in
  SUBMISSION.md with both commit ids; the LoRA SFT experiment is documented and not used at
  inference.
- Generalisation: `experiments/ext40` scores 26/40 with the submitted harness vs 87% on the 400;
  ~3 points self-inflicted value rules, ~2–3 label noise, the rest a real gap concentrated in
  cell-level lookups. Run-to-run variance is ~3–4 tasks per 40.
- Branch `prompt-fixes` (NOT merged): copy-verbatim value rules + source-aware whitespace check +
  medium-effort retry; recovers 19/52 of the 400's failures, neutral on ext40 (25 vs 26). First
  change to apply after the hackathon, with a two-run evaluation.
- Credits: roughly $55 for the 400 run, ~$25 for dev/ext40/targeted runs, ~$12 for the SFT; all
  well under the $1,000 budget.
- After the deadline: merge `prompt-fixes` and rerun the 400 twice; add an exploration turn
  before the script for cell-level lookup tasks; formula mode with LibreOffice recalculation in
  the container.

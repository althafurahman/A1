# A1 shared working memory

Updated: 2026-09-05 (evening, after dev16 batch). Record facts, not assumed progress.

## Current state

- Two-person team: user owns product/architecture/data/AI/ML; partner is senior full-stack developer.
- Registered for Research track. User also uses Claude Code for development.
- Team repo https://github.com/althafurahman/A1 cloned into A1/. Parent workspace holds the briefing PDFs and is not a Git repository.
- Work is on branch `baseline-setup` (from `main` at a2f6ea9), pushed to https://github.com/althafurahman/A1/tree/baseline-setup on 2026-09-05. `main` untouched; merging is a team decision.
- Starter imported: `research/` copied byte-identical from https://github.com/ylookup/encode-hackathon commit 37d9016264762a25cae49e077cd0893055bd9093 (verified with diff -r; remote HEAD was still that commit on 2026-09-05). Root `.gitattributes` copied too. See `research/UPSTREAM.md`. The temporary review checkout in /tmp is not the team project.
- Team `.gitignore` rule `data/` was changed to `/data/` so `research/data/download.py` is tracked; the downloaded dataset and tarball stay ignored.
- Environment verified on user's Mac (Darwin 25.6, Apple Silicon Homebrew):
  - uv 0.10.10; `uv sync --extra tinker` done in `research/` → venv Python 3.13.12, tinker 0.27.1, tinker-cookbook 0.5.7, openpyxl 3.1.5, pydantic-ai-slim 2.38.0 (from starter uv.lock).
  - Dataset downloaded and checksum OK: `research/data/spreadsheetbench_verified_400/` (400 tasks).
  - `uv run evaluate.py --oracle` → items 400, graded 400, pass_rate 1.0, cell_accuracy 1.0 (grader loads/compares correctly; says nothing about model ability).
  - LibreOffice 26.8.0.3 installed via `brew install --cask libreoffice`; `soffice` on PATH. Recalculation verified: a formula written by openpyxl with no cached value came back as the correct number through `sb.recalculate()`.
  - Docker Desktop 29.1.2 installed; daemon started with `open -a Docker` and responds. It must be running for any future code-executing agent.
- Model identifier CONFIRMED by user 2026-09-05: `Qwen/Qwen3.8-27B` (Tinker models page: about $1.86/M prefill, $5.60/M sample; tinker-cookbook renderer `qwen3_8_xhigh_reasoning`). Recorded in `research/.env` as A1_ALLOWED_MODEL_ID. No model has been called yet.
- Tinker access works: TINKER_API_KEY and TINKER_PROJECT_ID are set in `research/.env` (git-ignored). First attempt without a project id failed with `400 This project is read-only` (org default project); log in `research/submissions/baseline-smoke-001/console.log`.
- Smoke test evidence (all committed, unchanged starter `baseline/tinker_predict.py`, model `Qwen/Qwen3.8-27B`, temperature 0, renderer `qwen3_8_xhigh_reasoning` = HF default):
  - `submissions/baseline-smoke-002/` (default `--max-tokens 8192`): both tasks hit exactly 8192 output tokens while still inside the think block, so no JSON was parsed; both status=error, init workbook copied as output, pass_rate 0.0. ~103 s per task.
  - `submissions/baseline-smoke-003/` (`--max-tokens 24576`): both parsed. 51-12 PASS (5271 out tokens, 63 s). 13-1 101/120 cells (12814 out tokens, 154 s). pass_rate 0.5, cell_accuracy 0.843. `results.json` saved.
  - 13-1's 19 misses are all dates: model returned strings like `2024-02-03 00:00:00`, starter writes them as text, golden has real datetimes. Starter README warns about this. Failure category: value typing at write time, not reasoning.
  - Same task/prompt gave 8192+ tokens in run 002 and 5271 in run 003: sampling varies even at temperature 0, as SUBMISSION.md notes.
  - Throughput ~80 output tokens/s per request. Sizing guess for 400 tasks at 24576 cap: 5k-13k output tokens/task -> roughly $15-30 of the $1,000 credits (sample $5.595/M); wall time ~3 h at concurrency 4. Concurrency/rate limits not yet known.
- Dev subset: `experiments/dev16.ids` = 16 tasks, 4 per bucket (cell/sheet x small/large answer range), seeded, excludes smoke ids. Untouched validation subset not yet defined.
- `submissions/dev16-baseline-001/` (unchanged starter, `--max-tokens 24576 --concurrency 8`, results.json saved): pass_rate 0.625 (10/16), cell_accuracy 0.516, cell-level 7/8, sheet-level 3/8. 0 request/transport failures. 2 truncated at the cap. Elapsed 1219 s (20 min) for 16 tasks; 144k output tokens; est. cost $0.85.
  - Throughput: aggregate ~118 output tok/s at concurrency 8 vs ~80 tok/s for a single request, so per-request speed fell to ~28 tok/s. Concurrency barely helps; looks like a project-level sampling rate limit. Full-400 projection at this config: ~3.6M output tokens, ~8.5 h, ~$21. Do not run the full 400 until absolutely needed (user decision 2026-09-05).
  - Failure categories from traces (6 fails): (a) truncation x2: 183-8 reasoning never converged in 24k tokens (weighted-average task), 57232 finished reasoning but ran out of tokens while emitting the 190-cell JSON; (b) row-shift/manipulation errors x2: 230-16 answer shifted one row, 156-14 wrong rows deleted; (c) misread task x1: 263-1 wrote category names instead of totals; (d) near miss x1: 203-15 missed header 'Total' in M1 (38/39). Plus from smoke 13-1: dates written as text.
  - Interpretation: sheet-level tasks with many cells are where the text-dump-and-enumerate approach fails: the model must reason about and re-emit every cell. Cell-level tasks are already strong.
- Credits spent so far: about $1.10 across smoke-001..003 and dev16-baseline-001.

## Open questions

1. Token cap: 8192 truncates; 24576 still truncates 2/16. Large answer ranges need either a bigger cap or an approach that does not enumerate cells in the reply.
2. Permitted training-data sources. Claude Code/Codex are development tools only, not solver models.
3. Judge runtime/resources/API limits; research video/live presentation expectations.
4. GCP endpoint in old README is unconfirmed and not needed for the Tinker route.
5. Tinker concurrency/rate limits (BASELINE step 1) still unknown; affects wall time of the full run.

## Decisions

- First milestone is baseline reproduction, not optimisation.
- Team checkout is A1/; parent retains source PDFs.
- Reuse starter code and official evaluator unchanged; use Tinker only with confirmed model.
- No fine-tuning initially. No UI or additional agent framework.
- Starter `tinker_predict.py` renderer for Qwen3.8 is a thinking renderer; `--max-tokens 8192` default may need raising if replies truncate (check traces before changing).

## A1 harness results (second Claude Code session, 2026-09-05 evening)

The code-executing agent proposed in the root README is now implemented in `a1/` and measured.
Pipeline per task: model writes an openpyxl script (INIT/OUT contract, values only) → script runs
in a scratch dir → mechanical hygiene checks (formula strings, stray whitespace) → LLM verify pass
shown the answer region BEFORE (init) and AFTER (output) → bounded repair loop (2) → direct
JSON-answer fallback only if the code path produced no output at all. Backend: Tinker,
`Qwen/Qwen3.8-27B`, temperature 0, max-tokens 24576. Root `.env` (not `research/.env`) feeds `a1/`.

- `experiments/smoke-a1-001/`: 13-1 and 51-12 both PASS (baseline: 13-1 failed on dates-as-text).
- `experiments/dev16-a1-001/`: dev16, concurrency 6 — pass_rate 0.875 (14/16), cell_accuracy 0.9865,
  cell-level 8/8, sheet-level 6/8. 34 model calls (16 code, 17 verify, 1 repair), 207k output tokens,
  ~24 min, ~$1.29. Both failures near-misses: 230-16 trailing whitespace in text values (7/12),
  156-14 two cells left empty (154/156).
- Fixes: whitespace hygiene check + strip rule; verifier now surfaced EMPTY cells and the
  before/after region comparison (row-shift detection); produced outputs are kept over the fallback;
  missing answer sheets are created by name, never written to the active sheet.
- `experiments/fix-check-001/`: 156-14 PASS 156/156. 230-16 regressed to 2/12 via a differently
  sampled script (row shift; sampling varies at temp 0) — motivated the before/after verifier.
- `experiments/fix-check-002/`: 230-16 PASS 12/12, first attempt, no repairs.
- `experiments/dev16-a1-002/`: confirmation run of the final config on dev16 — pass_rate 0.9375
  (15/16), cell_accuracy 0.971, cell-level 8/8, sheet-level 7/8. 32 calls, 248k output tokens,
  ~$1.52. Sole failure 183-8 (5/20, region partially empty) — it passed in dev16-a1-001;
  sampling variance at temperature 0, same wobble the baseline shows. Every dev16 task has now
  passed with the final config in at least one run.
- Credits spent by these runs: ~$3.50 total.
- Cosmetic: tinker's session-futures poller logs "Task was destroyed but it is pending!" at exit;
  harmless, not yet silenced.
- Full-400 projection at this config: ~5M output tokens, ~$30, ~9-10 h at the observed rate cap.
  NOT launched — user decision 2026-09-05 evening: hold pending team discussion. It must start
  Saturday night to leave margin before the Sunday 12:00 deadline.
- Code review of PR #1 completed (15 verified findings; top items: research/README quick start +
  llm_predict default use forbidden DeepSeek, BASELINE.md step-4 omits --max-tokens, BASELINE.md
  $A1_ALLOWED_MODEL_ID never reaches the shell, root-vs-research .env mismatch). Findings shared
  with the user; team-authored doc fixes still to apply.

## Docker and submission prep (user's session, 2026-09-06 01:00-01:35)

- Docker image built and run exactly per the judge contract (`/data` read-only, empty `/out`, keys via env): tasks 51-12 and 79-7 both status ok and PASS under the shipped evaluator; traces carry every required field plus phase/tool lines; no `golden` string in prompts or traces.
- Dockerfile hardened without changing pipeline behaviour: CPU-only torch index (image 9.75 GB -> 2.06 GB; avoids CUDA wheels on x86 judge machines) and the Qwen3.8 tokenizer baked at build time so start-up does not depend on Hugging Face.
- Cost profile seen in-container: a 1-cell task spent 17,929 output tokens (366 s) in the code call at default (xhigh) reasoning effort; the verify call 1,248 tokens. Reasoning effort is the main time lever if a rerun is ever needed.
- `scripts/finalize.sh <run dir>`: scores with `--all`, copies predictions/outputs/traces/run.log/results.json to the repo root, greps traces for `golden`. `scripts/analyse_run.py <run dir>`: per-task calls/tokens/time and failure buckets.
- `SUBMISSION.md` drafted for the Tinker pipeline (model id, env vars, trace truncation declared, evidence paths that exist). Still to fill: member handles and the scores block.

## Full-400 run (night of 2026-09-05→06) — SUBMITTED ARTIFACTS

Final score, shipped evaluator, `--all`, recalculation on: **pass_rate 0.870, cell_accuracy
0.9729, cell-level 0.9091, sheet-level 0.784** (items 400, missing 0). Artifacts at repo root
(`predictions.jsonl`, `outputs/`, `traces/`, `run.log`, `results.json`); merged set also kept
in `experiments/submission-run/`.

Chronology (disclosed in SUBMISSION.md): the run executed in four segments, merged last-wins
on non-ok status; completed answers were never re-rolled.
- `full-400-001` (00:39, concurrency 16): killed externally at 253/400. Observed 470→820 tok/s
  aggregate — the assumed ~140 tok/s project cap was wrong; throughput scales with concurrency
  and off-peak hours. 17 errors, mostly context-window overflows on giant workbooks.
- Mid-run fix (committed a76d3a5, solver prompts unchanged for normal tasks): Tinker serves the
  model with a 64k context, not 1M — clamp max_tokens to fit, shrink serialization on overflow
  (120k→45k→16k chars), and route no-code-block replies through the repair nudge.
- `full-400-002` (concurrency 10): killed at 10 tasks. Both kills took session-managed
  background tasks only — machine never slept (60d uptime); cause is the session task sweep,
  not OOM. Lesson: long runs must be nohup-detached from the session.
- `full-400-003` (detached, concurrency 10): survived but slow (~250 tok/s); killed by us.
- `full-400-004` (detached, concurrency 16): 144 tasks, zero kill, finished 03:50. The former
  overflow errors passed with the fix (80-42, 209-30, 455-35, 41-47...).
- Remaining failures: 2/400 with no answer (118-50, 42216 — model exhausts budget thinking
  about 5000-row ranges before emitting code; init copies stand in, status honest).
- Night's spend: ~7.6M output tokens, ≈$45. Total credits used to date ≈$55 of $1,000.

## LoRA SFT experiment (user's session, branch `lora-sft`, 2026-09-06 04:40-06:00)

Goal: a model-side improvement feasible in the remaining hours, following the Tinker talk's text-to-SQL lesson (put task expertise into weights, cut test-time scaffolding). RL was ruled out by arithmetic (one GRPO step at ~15k thinking tokens per sample is ~8M tokens, ~18 h at the shared rate). Chosen: rejection-sampling SFT on the harness's own verified outputs, trained to emit the script with an empty think block.

- Data: `scripts/build_sft.py` rebuilt the exact inference prompt for every task that PASSED in the 400 run and is not in `experiments/heldout78.ids` (78 stratified held-out ids incl. dev16); target = the code/repair reply that produced the last successful script. 258 examples, 665k tokens (median 1,852/example), 17 skipped as too long, 5 without a usable reply, 10 samples hand-audited (all read the workbook, none hard-code answers). Golden files were used only to SELECT examples; disclosed in SUBMISSION.md.
- Training: `scripts/train_sft.sh sft-001` = cookbook `chat_sl` recipe, `Qwen/Qwen3.8-27B`, LoRA rank 32, lr 2e-4, batch 32, 2 epochs = 16 steps, 1.34M elapsed tokens, ~4 s/step, final train NLL 0.205 (from 0.228). Checkpoint (no TTL): `tinker://17741918-b3a7-5ae6-bf92-9556e1033720:train:0/sampler_weights/final`. Cost about $6.
- Evaluation `experiments/heldout78-sft-001/` (same harness, `--model-path`, concurrency 16, ~10 min, ~$3.5) vs the base model's own results on the same 78 ids from the 400 run:

  | | base model | fine-tuned |
  |---|---|---|
  | pass | 68/78 | 52/78 |
  | cell-level / sheet-level pass | 35/40, 33/38 | 27/40, 25/38 |
  | cell_accuracy | ~0.97 | 0.986 |
  | mean output tokens/task | 18,104 | 1,313 |
  | mean model seconds/task | 335 | 50 |
  | mean model calls/task | 2.28 | 3.47 |

- Reading: the fine-tune keeps the code style and speed (14x fewer tokens, 7x faster) but loses the reasoning that decides *what* to compute: failures are interpretation errors (wrong count rule, wrong rows), not truncation or plumbing; 20 of 26 failures are partial (high cell accuracy). Because verify/repair use the same no-think model, the verifier also weakened: it passed 12 of the 26 failing outputs, and 9 tasks looped through repair without converging. Won 2 tasks the base missed (51090, 37900), lost 18.
- Decision per the pre-agreed gate (within 2 tasks of base): NOT used for the submission. The base-model 400 run on `main` stands. Documented as an experiment. Natural follow-ups (not attempted, no time): cascade (fine-tuned first, base model when the verifier rejects), keep the base model for the verify phase, or SFT targets that retain a short thinking trace.

## Collaboration

Claude Code (user's session) edited on branch `baseline-setup`: `.gitignore`, `MEMORY.md`, `research/` import. Second Claude Code session (this one) rebased the `a1/` harness work onto `baseline-setup` and pushed; it currently claims `a1/*`, root `README.md`, `MEMORY.md`. SUBMISSION.md claim settled: the 00:45 draft and the post-run scores were merged during the 04:30 rebase; no file currently claimed. Before concurrent edits, record owner and files here, then release when finished. Do not duplicate paid experiments.

## Next action (Sunday morning)

1. SUBMISSION.md is complete (both handles, scores, write-up merged from both drafts).
2. Team: merge PR #1 into main.
3. Apply the PR-review doc fixes (DeepSeek quick-start warning, BASELINE.md --max-tokens and
   env-var interpolation, .env location note) — 15 min, doc-only.
4. Submit the repo URL through the organiser form BEFORE 12:00. The full-400 run, scores,
   artifacts and SUBMISSION.md are DONE — do not re-run anything paid without a team decision.

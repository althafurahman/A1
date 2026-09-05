# A1 shared working memory

Updated: 2026-09-05 (evening, after smoke tests). Record facts, not assumed progress.

## Current state

- Two-person team: user owns product/architecture/data/AI/ML; partner is senior full-stack developer.
- Registered for Research track. User also uses Claude Code for development.
- Team repo https://github.com/althafurahman/A1 cloned into A1/. Parent workspace holds the briefing PDFs and is not a Git repository.
- Work is on local branch `baseline-setup` (branched from `main` at a2f6ea9). Nothing pushed.
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
- Credits spent so far: three sampling calls plus one failed session, roughly $0.20.

## Open questions

1. Which `--max-tokens` to use for the full baseline: 8192 default demonstrably truncates; 24576 worked on both smoke tasks. Sheet-level tasks with big answer ranges may need more. Decide before the 400 run.
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

## Collaboration

Claude Code (user's session) edited on branch `baseline-setup`: `.gitignore`, `MEMORY.md`, `research/` import. No files currently claimed. Before concurrent edits, record owner and files here, then release when finished. Do not duplicate paid experiments.

## Next action

1. Confirm `--max-tokens` and concurrency with the user, then BASELINE step 4: full 400 into fresh `submissions/baseline-full-001/`, run with `2>&1 | tee submissions/baseline-full-001/console.log`.
2. Run BASELINE.md step 3 smoke test (`--ids 13-1,51-12`) from `research/`, then step 4 full 400 into a fresh `submissions/baseline-full-001/` directory, capturing stdout/stderr with `2>&1 | tee`.
3. Record model, parameters, elapsed time, token usage, errors and the evaluator summary here.

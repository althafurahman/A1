# A1 shared working memory

Updated: 2026-09-05 (evening). Record facts, not assumed progress.

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
- Model identifier: Tinker's public models page (https://tinker-docs.thinkingmachines.ai/tinker/models/) lists `Qwen/Qwen3.8-27B` (about $1.86/M prefill, $5.60/M sample) and tinker-cookbook maps it to renderer `qwen3_8_xhigh_reasoning`. This matches the organiser's display name but the user has NOT yet confirmed it as the permitted identifier. No model has been called.
- No TINKER_API_KEY configured (no `.env` in A1/ or research/). No credits spent, no training, no scores produced.

## Open questions

1. Confirm `Qwen/Qwen3.8-27B` is the exact permitted identifier (organiser or Tinker project). Then set A1_ALLOWED_MODEL_ID and TINKER_API_KEY in `research/.env` (never committed).
2. Permitted training-data sources. Claude Code/Codex are development tools only, not solver models.
3. Judge runtime/resources/API limits; research video/live presentation expectations.
4. GCP endpoint in old README is unconfirmed and not needed for the Tinker route.

## Decisions

- First milestone is baseline reproduction, not optimisation.
- Team checkout is A1/; parent retains source PDFs.
- Reuse starter code and official evaluator unchanged; use Tinker only with confirmed model.
- No fine-tuning initially. No UI or additional agent framework.
- Starter `tinker_predict.py` renderer for Qwen3.8 is a thinking renderer; `--max-tokens 8192` default may need raising if replies truncate (check traces before changing).

## Collaboration

Claude Code (user's session) edited on branch `baseline-setup`: `.gitignore`, `MEMORY.md`, `research/` import. No files currently claimed. Before concurrent edits, record owner and files here, then release when finished. Do not duplicate paid experiments.

## Next action

1. User confirms model identifier and puts TINKER_API_KEY in `research/.env`.
2. Run BASELINE.md step 3 smoke test (`--ids 13-1,51-12`) from `research/`, then step 4 full 400 into a fresh `submissions/baseline-full-001/` directory, capturing stdout/stderr with `2>&1 | tee`.
3. Record model, parameters, elapsed time, token usage, errors and the evaluator summary here.

# A1 — SpreadsheetBench Harness

Team A1's entry for the **Ylookup × Encode AI Hackathon** (research track): make a small
model genuinely good at real spreadsheet work. The benchmark is SpreadsheetBench
Verified — 400 tasks scraped from Excel forums. Workbook in, workbook out, graded
cell-for-cell against a golden workbook after recalculation.

**Result:** pass_rate **0.870** on all 400 tasks (cell accuracy 0.9729), against the
59.0% one-shot reference baseline. Method, scores and artifact paths:
[SUBMISSION.md](SUBMISSION.md). Dated lab notebook of every run, failure category and
decision: [MEMORY.md](MEMORY.md).

## Approach

A code-executing agent around the fixed competition model, Qwen3.8-27B (temperature 0):
instead of answering from a truncated text dump of the sheet, the model writes a Python
script that opens the actual workbook, computes the result, and writes plain values into
the graded answer region — wrapped in an execute → repair loop (mechanical hygiene checks
plus a before/after self-verification pass) and a direct-answer fallback when the code
path produces nothing. Fine-tuned checkpoints of the same model run through Tinker
(Thinking Machines Lab).

## Layout

```
a1/                 harness source
  run.py            entrypoint: reads /data, writes /out (judge contract)
  harness.py        per-task pipeline: code agent, repair, verify, fallback
  serialize.py      answer-region-aware workbook serialization
  coderun.py        sandboxed execution of model-written scripts
  tinker_llm.py     Tinker sampling backend (primary model access)
  sbio.py           dataset + answer-range plumbing
experiments/        dev-set runs and results (dev16 comparisons, fix checks)
research/           official starter, imported unchanged (see research/UPSTREAM.md)
Dockerfile          the container judges run: /data (ro) -> /out
SUBMISSION.md       method write-up, models, scores
.env.example        environment variables the pipeline needs
```

## Run

```sh
uv sync
uv run python -m a1.run --dataset-dir <dataset> --out-dir <out> [--ids 13-1,51-12]
```

Or via Docker (the judge contract):

```sh
docker build -t a1 .
docker run --rm --env-file .env -v <dataset dir>:/data:ro -v <empty dir>:/out a1
```

Credentials: copy `.env.example` to `.env` **at the repo root** (read by `a1/`), and note
the imported starter scripts read `research/.env` instead — keep both in sync if you use
both. Tinker is the confirmed access route (`TINKER_API_KEY` + `TINKER_PROJECT_ID`);
the model is fixed to Qwen3.8-27B and `a1/run.py` warns on anything else. Keys never
live in the repo.

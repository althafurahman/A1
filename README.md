# A1 — SpreadsheetBench Harness

Team A1's entry for the **Ylookup × Encode AI Hackathon** (research track): make a small
model genuinely good at real spreadsheet work. The benchmark is SpreadsheetBench
Verified — 400 tasks scraped from Excel forums. Workbook in, workbook out, graded
cell-for-cell against a golden workbook after recalculation.

## Approach

**Status:** project scaffold only; the architecture below is proposed, not yet implemented or measured. Start with [PROJECT.md](PROJECT.md), [BASELINE.md](BASELINE.md) and [MEMORY.md](MEMORY.md). Claude Code should read [CLAUDE.md](CLAUDE.md); shared development instructions are in [AGENTS.md](AGENTS.md).

A code-executing agent around the fixed competition model, Qwen3.8-27B (temperature 0):
instead of answering from a truncated text dump of the sheet, the model writes a Python
script that opens the actual workbook, computes the result, and writes plain values into
the graded answer region — wrapped in an execute → repair loop, a self-verification
pass, and a direct-answer fallback. Fine-tuned checkpoints of the same model run through
Tinker (Thinking Machines Lab). Details land here with the code.

## Layout

```
a1/                 harness source
  run.py            entrypoint: reads /data, writes /out (judge contract)
  harness.py        per-task pipeline: code agent, repair, verify, fallback
  serialize.py      answer-region-aware workbook serialization
  coderun.py        sandboxed execution of model-written scripts
  llm.py            chat-completions client for the team's model endpoint
  tinker_llm.py     Tinker sampling backend for fine-tuned checkpoints
  sbio.py           dataset + answer-range plumbing
experiments/        dev-set ablation runs and results
Dockerfile          the container judges run: /data (ro) -> /out
SUBMISSION.md       method write-up, models, scores
.env.example        environment variables the pipeline needs
```

## Run

```sh
docker build -t a1 .
docker run --rm --env-file .env -v <dataset dir>:/data:ro -v <empty dir>:/out a1
```

The Docker command above is the intended run contract; a Dockerfile has not been implemented yet.

Copy `.env.example` to `.env` and configure only the confirmed team access route. Tinker supports baseline sampling as well as optional fine-tuning. A GCP-hosted model endpoint is not confirmed or required by the supplied instructions. Obtain the exact allowed Qwen3.8-27B API identifier before any model call. Keys never live in the repo.

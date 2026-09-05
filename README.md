# A1 — SpreadsheetBench harness

Team A1's entry for the Ylookup x Encode hackathon research track. A code-executing
agent around `qwen/qwen3.8-27b` (temperature 0): the model writes a Python script that
opens the real workbook, computes the result, and writes plain values into the graded
answer region; the script runs in the container, failures feed back for repair, and a
reviewer call checks the written region against the instruction before accepting.
A direct JSON-answer fallback covers tasks where the code path fails.

## Run

```sh
docker build -t a1 .
docker run --rm --env-file .env -v <dataset dir>:/data:ro -v <empty dir>:/out a1
```

The dataset dir must hold `dataset.json` and `spreadsheet/<id>/` folders as in
`spreadsheetbench_verified_400`. Results land in `/out`: `predictions.jsonl`,
`outputs/`, `traces/`, `run.log`.

Local, without Docker (model-written code then runs on your machine):

```sh
uv sync
uv run python -m a1.run --dataset-dir <dataset> --out-dir <out> --ids 13-1,51-12
```

`OPENROUTER_API_KEY` comes from the environment or a repo-root `.env`.

## Layout

- `a1/run.py` — entrypoint and output-contract plumbing
- `a1/harness.py` — per-task pipeline: code agent, repair loop, verifier, direct fallback
- `a1/serialize.py` — answer-region-aware workbook serialization (values + formula overlay)
- `a1/coderun.py` — sandboxed execution of the model's script
- `a1/llm.py` — OpenRouter client, fixed model, temperature 0
- `a1/sbio.py` — dataset/answer-range plumbing, adapted from the official starter

Scores, method and experiments: see [SUBMISSION.md](SUBMISSION.md).

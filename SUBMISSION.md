# Submission: A1

## Team

- Team name: A1
- Members, one GitHub handle per line:
  - (fill in)
- Repo URL: (fill in)

## What we built and why

(150–300 words — filled in before submission.)

## Models

- `qwen/qwen3.8-27b`, temperature 0, for every call in the pipeline
  (code generation, repair, verification, direct fallback). Endpoint named before submission.

## Scores on the 400

```json
(paste the summary block of results.json here)
```

## Your run on the 400

- `predictions.jsonl`: repo root
- `outputs/`: repo root
- `traces/`: repo root, one `<id>.jsonl` per task, one line per model call or tool step
- `run.log`: repo root

## Code

The pipeline is an agent that executes model-written Python, so it runs in Docker:

```sh
docker build -t a1 .
docker run --rm --env-file .env -v <dataset dir>:/data:ro -v <empty dir>:/out a1
```

Environment variables: `A1_API_BASE`, `A1_API_KEY` (the team's model endpoint).

## Things to look at

- `experiments/` — dev-set ablations (60 stratified tasks): baseline vs direct vs code vs full, results.json per config
- `a1/serialize.py` — answer-region-aware serialization; why the one-shot baseline is blind on 80/400 workbooks

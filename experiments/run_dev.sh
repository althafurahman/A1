#!/usr/bin/env bash
# Run one harness config on the dev set and score it with the official evaluator.
#   ./experiments/run_dev.sh <name> [--strategy code|direct|full] [--concurrency N] [--ids id1,id2]
# Results land in experiments/<name>/ (outputs, traces, predictions, results.json).
set -euo pipefail
cd "$(dirname "$0")/.."

NAME=$1; shift
RESEARCH="${RESEARCH:-../encode-hackathon/research}"
DATASET="${DATASET:-$RESEARCH/data/spreadsheetbench_verified_400}"
IDS=$(cat experiments/devset.txt)

uv run python -m a1.run --dataset-dir "$DATASET" --out-dir "experiments/$NAME" --ids "$IDS" "$@"

(cd "$RESEARCH" && uv run evaluate.py \
    --predictions "$OLDPWD/experiments/$NAME/predictions.jsonl" \
    --out "$OLDPWD/experiments/$NAME/results.json" --quiet)

python3 -c "import json; print('$NAME:', json.load(open('experiments/$NAME/results.json'))['summary'])"

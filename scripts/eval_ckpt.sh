#!/usr/bin/env bash
# Run the a1 harness with a Tinker sampler checkpoint on the held-out 78 and score it.
#   scripts/eval_ckpt.sh tinker://<run>/sampler_weights/<name> heldout78-sft-001 [--concurrency 16]
set -euo pipefail
cd "$(dirname "$0")/.."
CKPT=${1:?tinker:// sampler path}; NAME=${2:?out name}; shift 2
mkdir -p "experiments/$NAME"
uv run --project research python -m a1.run --base-model Qwen/Qwen3.8-27B --model-path "$CKPT" \
    --dataset-dir research/data/spreadsheetbench_verified_400 --out-dir "experiments/$NAME" \
    --ids "$(cat experiments/heldout78.ids)" --concurrency "${CONCURRENCY:-16}" "$@" 2>&1 | tee "experiments/$NAME/console.log"
(cd research && uv run evaluate.py --predictions "../experiments/$NAME/predictions.jsonl" --out "../experiments/$NAME/results.json" --quiet 2>/dev/null)
python3 scripts/analyse_run.py "experiments/$NAME" | tail -6

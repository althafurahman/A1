#!/usr/bin/env bash
# LoRA SFT of Qwen3.8-27B on experiments/<name>/train.jsonl with the cookbook recipe (no custom loop).
#   scripts/train_sft.sh sft-001 [extra key=value overrides]
set -euo pipefail
cd "$(dirname "$0")/.."
NAME=${1:?experiment name}; shift || true
set -a; source research/.env; set +a
uv run --project research python -m tinker_cookbook.recipes.chat_sl.train \
    model_name=Qwen/Qwen3.8-27B dataset="$PWD/experiments/$NAME/train.jsonl" \
    learning_rate=2e-4 batch_size=32 lora_rank=32 max_length=16384 num_epochs=2 \
    save_every=10 eval_every=10 log_path="$PWD/experiments/$NAME/log" "$@" 2>&1 | tee "experiments/$NAME/train.log"
echo "checkpoints:"; tail -3 "experiments/$NAME/log/checkpoints.jsonl"

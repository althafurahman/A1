#!/usr/bin/env bash
# Score a finished full run with the shipped evaluator and copy the submission artefacts to the repo root.
#   scripts/finalize.sh experiments/full-400-001
set -euo pipefail
cd "$(dirname "$0")/.."
RUN=${1:?run dir, e.g. experiments/full-400-001}
test -s "$RUN/predictions.jsonl" || { echo "no predictions in $RUN"; exit 1; }
echo "predictions: $(wc -l < "$RUN/predictions.jsonl") lines; not-ok: $(grep -vc '"status": "ok' "$RUN/predictions.jsonl" || true)"
(cd research && uv run evaluate.py --predictions "../$RUN/predictions.jsonl" --all --out "../$RUN/results.json" --quiet 2>/dev/null)
python3 -c "import json; print(json.dumps(json.load(open('$RUN/results.json'))['summary']))"
rm -rf outputs traces
cp -R "$RUN/outputs" outputs
cp -R "$RUN/traces" traces
cp "$RUN/predictions.jsonl" "$RUN/run.log" "$RUN/results.json" .
echo "copied predictions.jsonl outputs/ traces/ run.log results.json to repo root"
grep -rl -i 'golden' traces/ | head -3 && echo "^^^ WARNING: 'golden' appears in traces; inspect before submitting" || echo "traces clean: no 'golden' string"

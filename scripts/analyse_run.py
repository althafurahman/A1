"""Summarise a harness run: per-task status, calls, tokens, time; failure buckets from results.json.
    python3 scripts/analyse_run.py experiments/full-400-001
"""
import json, sys, glob, os, collections
d = sys.argv[1]
preds = {json.loads(l)["id"]: json.loads(l) for l in open(f"{d}/predictions.jsonl") if l.strip()}
res = {i["id"]: i for i in json.load(open(f"{d}/results.json"))["items"]} if os.path.exists(f"{d}/results.json") else {}
rows, tot_out, tot_in = [], 0, 0
for f in glob.glob(f"{d}/traces/*.jsonl"):
    tid = os.path.basename(f)[:-6]
    recs = [json.loads(l) for l in open(f) if l.strip()]
    calls = [r for r in recs if r.get("model")]
    out = sum(r.get("output_tokens") or 0 for r in calls); inp = sum(r.get("input_tokens") or 0 for r in calls)
    phases = collections.Counter(r.get("phase") for r in calls)
    secs = sum(r.get("latency_ms") or 0 for r in calls) / 1000
    r = res.get(tid, {})
    rows.append((tid, r.get("type", "?")[:5], preds.get(tid, {}).get("status", "?")[:40], len(calls), dict(phases), out, secs,
                 f"{r.get('correct')}/{r.get('cells')}" if "cells" in r else r.get("status", ""), bool(r.get("pass"))))
    tot_out += out; tot_in += inp
rows.sort(key=lambda x: (x[8], -x[5]))
print(f"{'id':<8} {'type':<6} {'pass':<5} {'score':<9} {'calls':>5} {'out_tok':>8} {'sec':>6}  status / phases")
for tid, typ, st, n, ph, out, secs, sc, ok in rows:
    print(f"{tid:<8} {typ:<6} {'PASS' if ok else '.':<5} {sc:<9} {n:>5} {out:>8} {secs:>6.0f}  {st} {ph}")
n = len(rows)
if n:
    print(f"\ntasks {n}  passed {sum(r[8] for r in rows)}  tokens in {tot_in} out {tot_out}  mean out/task {tot_out//n}")
    print(f"est cost ${tot_in/1e6*1.86 + tot_out/1e6*5.595:.2f}")
    fails = [r for r in rows if not r[8]]
    buckets = collections.Counter("status-error" if r[2].startswith("error") else ("partial" if r[7] not in ("", None) and "/" in r[7] and r[7].split("/")[0] not in ("0", "None") else "wrong") for r in fails)
    print("failure buckets:", dict(buckets))
if res:
    print(json.dumps(json.load(open(f"{d}/results.json"))["summary"]))

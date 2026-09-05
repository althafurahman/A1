"""Team A1 pipeline entrypoint.

    python -m a1.run --dataset-dir /data --out-dir /out [--ids 13-1,51-12] [--concurrency 8] [--strategy full]

Reads dataset.json + init workbooks from --dataset-dir, writes predictions.jsonl,
outputs/, traces/ and run.log into --out-dir. Needs OPENROUTER_API_KEY.
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

from .harness import TaskRunner
from .llm import MODEL, Client
from .sbio import load_dataset


def load_env():
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-dir", default="/data")
    p.add_argument("--out-dir", default="/out")
    p.add_argument("--ids", help="comma-separated task ids (default: all)")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--strategy", choices=["full", "code", "direct"], default="full",
                   help="full = code agent + verify + direct fallback; others for ablations")
    p.add_argument("--model", default=os.environ.get("MODEL", MODEL),
                   help="override for ablations only; the submission model is fixed")
    return p.parse_args()


def prepare_out_dir(out_dir: Path):
    for sub in ("outputs", "traces"):
        shutil.rmtree(out_dir / sub, ignore_errors=True)
        (out_dir / sub).mkdir(parents=True)
    for name in ("predictions.jsonl", "run.log"):
        (out_dir / name).write_text("", encoding="utf-8")


def append_jsonl(path: Path, record: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log(out_dir: Path, line: str):
    print(line, flush=True)
    with (out_dir / "run.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


async def main():
    load_env()
    args = parse_args()
    out_dir = Path(args.out_dir)
    prepare_out_dir(out_dir)

    tasks = load_dataset(args.dataset_dir)
    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",") if i.strip()}
        tasks = [t for t in tasks if t["id"] in wanted]

    client = Client(model=args.model)
    log(out_dir, f"A1 model={args.model} strategy={args.strategy} tasks={len(tasks)} concurrency={args.concurrency}")
    semaphore = asyncio.Semaphore(args.concurrency)

    async def run_one(task):
        async with semaphore:
            runner = TaskRunner(client, task, out_dir, strategy=args.strategy)
            try:
                status = await runner.solve()
            except Exception as e:  # keep the run alive; a task without a line scores zero
                shutil.copy(task["init_xlsx"], runner.out_xlsx)
                status = f"error: {type(e).__name__}: {e}"[:200]
            for rec in runner.traces:
                append_jsonl(out_dir / "traces" / f"{task['id']}.jsonl", rec)
            append_jsonl(out_dir / "predictions.jsonl",
                         {"id": task["id"], "output": f"outputs/{task['id']}.xlsx", "status": status})
            log(out_dir, f"{task['id']:<8} {status}")

    await asyncio.gather(*(run_one(t) for t in tasks))
    done = sum(1 for _ in (out_dir / "predictions.jsonl").read_text().splitlines())
    log(out_dir, f"finished: {done}/{len(tasks)} predictions written")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)

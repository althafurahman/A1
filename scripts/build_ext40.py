"""Build experiments/ext40: 40 unseen tasks from the original SpreadsheetBench 912 that are not in the Verified 400.
    uv run --project research python scripts/build_ext40.py [--exclude id1,id2] [--n 40]
Tarball: research/data/spreadsheetbench_912_v0.1.tar.gz (downloaded if missing). Output layout matches the Verified set.
"""
import argparse, hashlib, json, random, re, shutil, sys, tarfile, urllib.request
from pathlib import Path
sys.path.insert(0, "research")
import openpyxl
from sb import answer_cells, load_answer_values, values_equal

URL = "https://huggingface.co/datasets/KAKA22/SpreadsheetBench/resolve/main/spreadsheetbench_912_v0.1.tar.gz?download=true"
DATA = Path("research/data"); TARBALL = DATA / "spreadsheetbench_912_v0.1.tar.gz"; SRC = DATA / "spreadsheetbench_912_v0.1"
VERIFIED = DATA / "spreadsheetbench_verified_400" / "dataset.json"
OUT = Path("experiments/ext40")
BAD_WORDS = re.compile(r"\b(RAND|RANDBETWEEN|TODAY|NOW)\s*\(|conditional format|highlight|colou?r|font|bold|italic|shading|fill the cell", re.I)

ap = argparse.ArgumentParser(); ap.add_argument("--exclude", default=""); ap.add_argument("--n", type=int, default=40); ap.add_argument("--seed", type=int, default=1)
args = ap.parse_args(); exclude = {i for i in args.exclude.split(",") if i}

if not TARBALL.exists():
    print("downloading ~95 MB"); urllib.request.urlretrieve(URL, TARBALL)
print(f"{TARBALL.name} sha256 {hashlib.sha256(TARBALL.read_bytes()).hexdigest()}")
if not SRC.exists():
    with tarfile.open(TARBALL) as tar: tar.extractall(DATA, filter="data")
    inner = next(p for p in DATA.iterdir() if p.is_dir() and p.name.startswith("all_data_912"))
    inner.rename(SRC)
rows = json.loads((SRC / "dataset.json").read_text())
verified = {str(t["id"]) for t in json.loads(VERIFIED.read_text())}
cands = [r for r in rows if str(r["id"]) not in verified]
print(f"original {len(rows)}  verified {len(verified)}  candidates {len(cands)}")

drop = {"excluded": 0, "empty_instruction": 0, "missing_files": 0, "unloadable": 0, "no_sheet": 0, "bad_range": 0, "unchanged": 0, "too_big": 0, "formatting/volatile": 0}
ok = []
for r in cands:
    tid = str(r["id"]); folder = SRC / r["spreadsheet_path"]
    init, gold = folder / f"1_{tid}_input.xlsx", folder / f"1_{tid}_answer.xlsx"
    if tid in exclude: drop["excluded"] += 1; continue
    if not (init.exists() and gold.exists()): drop["missing_files"] += 1; continue
    if len((r.get("instruction") or "").strip()) < 20: drop["empty_instruction"] += 1; continue
    if BAD_WORDS.search(r["instruction"] or ""): drop["formatting/volatile"] += 1; continue
    t = dict(r, id=tid, init_xlsx=str(init), golden_xlsx=str(gold))
    try:
        wg = openpyxl.load_workbook(gold, read_only=True, data_only=True)
        sheet = t.get("answer_sheet")
        if sheet and sheet not in wg.sheetnames: drop["no_sheet"] += 1; continue
        cells = answer_cells(t, openpyxl.load_workbook(gold, read_only=True))
        if not cells: drop["bad_range"] += 1; continue
        if len(cells) > 2000: drop["too_big"] += 1; continue
        g = load_answer_values(gold, t); i = load_answer_values(init, t)
    except Exception:
        drop["unloadable"] += 1; continue
    if all(values_equal(g[k], i.get(k)) for k in g): drop["unchanged"] += 1; continue
    ok.append((t, len(cells)))
print("dropped:", drop, " eligible:", len(ok))

random.seed(args.seed)
buckets = {}
for t, n in ok: buckets.setdefault((t["instruction_type"][:5], "small" if n <= 15 else "large"), []).append((t, n))
per = args.n // 4; picked = []
for k in sorted(buckets):
    b = sorted(buckets[k], key=lambda x: x[0]["id"]); random.shuffle(b); picked += b[:per]
    print(f"  bucket {k}: eligible {len(b)}, taking {min(per, len(b))}")
# top up from largest buckets if some bucket was short
if len(picked) < args.n:
    rest = [x for k in buckets for x in buckets[k] if x not in picked]; random.shuffle(rest); picked += rest[: args.n - len(picked)]

if OUT.exists(): shutil.rmtree(OUT / "spreadsheet", ignore_errors=True)
(OUT / "spreadsheet").mkdir(parents=True, exist_ok=True)
out_rows = []
for t, n in picked:
    tid = t["id"]; d = OUT / "spreadsheet" / tid; d.mkdir()
    shutil.copy(t["init_xlsx"], d / f"1_{tid}_init.xlsx"); shutil.copy(t["golden_xlsx"], d / f"1_{tid}_golden.xlsx")
    (d / "prompt.txt").write_text(t["instruction"], encoding="utf-8")
    out_rows.append({k: t.get(k) for k in ("id", "instruction", "spreadsheet_path", "instruction_type", "answer_position", "answer_sheet", "data_position")})
    out_rows[-1]["spreadsheet_path"] = f"spreadsheet/{tid}"
(OUT / "dataset.json").write_text(json.dumps(out_rows, indent=1, ensure_ascii=False))
print(f"\nwrote {len(out_rows)} tasks to {OUT}\n")
print(f"{'id':<10} {'type':<6} {'cells':>5}  instruction")
for t, n in picked: print(f"{t['id']:<10} {t['instruction_type'][:5]:<6} {n:>5}  {t['instruction'][:90].replace(chr(10),' ')}")

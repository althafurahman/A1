# A1 lab notebook

Chronological record of the weekend: what we did at each stage, what we observed, and what
we decided to do next. All runs referenced here are committed under `experiments/` or
`research/submissions/` with their `results.json`.

---

## 1. Setup and evaluation plumbing — Sat afternoon

**Steps.** Imported the official starter byte-identical into `research/` (upstream commit
`37d9016`, verified with `diff -r`; see `research/UPSTREAM.md`). Installed the toolchain
(uv, Python 3.13, tinker 0.27.1, openpyxl 3.1.5, LibreOffice 26.8, Docker 29.1), downloaded
the 400-task dataset (checksum OK), and validated the grader before any model call:
`evaluate.py --oracle` and a LibreOffice recalculation round-trip on a formula with no
cached value.

**Observations.** Oracle scored 1.0 on all 400, recalculation returned the correct number —
the scoring pipeline is trustworthy. Confirmed the permitted model id on the Tinker models
page: `Qwen/Qwen3.8-27B` (~$1.86/M prefill, $5.60/M sample; renderer
`qwen3_8_xhigh_reasoning`). First Tinker call failed with `400 This project is read-only`
until `TINKER_PROJECT_ID` was set (org default project is read-only; log in
`research/submissions/baseline-smoke-001/console.log`). Profiled the dataset: 80/400
workbooks exceed the starter's 120×30 serialisation window; 359/400 answers are multi-cell
ranges; 105 workbooks are multi-sheet.

**Next steps.** Reproduce the unchanged baseline before touching anything; smoke test on 2
tasks, then a stratified dev subset.

## 2. Baseline reproduction — Sat evening

**Steps.** Ran the unchanged starter (`baseline/tinker_predict.py`, temperature 0) on tasks
13-1 and 51-12 at the default `--max-tokens 8192` (`baseline-smoke-002`), then at 24576
(`baseline-smoke-003`). Built `experiments/dev16.ids` — 16 tasks, 4 per bucket
(cell/sheet × small/large answer range), seeded, excluding smoke ids — and ran the baseline
on it (`research/submissions/dev16-baseline-001`).

**Observations.** At 8192 both smoke tasks truncated *inside the think block* — zero JSON,
pass_rate 0.0 (~103 s/task). At 24576: 51-12 PASS; 13-1 101/120 — all 19 misses were dates
returned as text where the golden holds real datetimes. Value typing at write time, not
reasoning. Dev16 baseline: **10/16 pass (62.5%), cell_accuracy 0.516**, cell-level 7/8,
sheet-level 3/8 (~20 min, ~$0.85). Failure categories from the traces: truncation ×2
(one never finished reasoning; one ran out of tokens while *enumerating a 190-cell JSON*),
row-shift ×2, misread ×1, near-miss ×1. Throughput ~118 tok/s aggregate at concurrency 8 —
read at the time as a project rate cap (later disproved, §6). Same prompt gave different
token counts across runs: sampling varies even at temperature 0.

**Next steps.** The failure taxonomy points away from prompt-polish and toward a
code-executing agent: sheet-level tasks fail because the model must re-emit every cell as
text. Build the agent; test one change at a time against dev16.

## 3. Code-executing harness — Sat evening

**Steps.** Implemented `a1/`: the model receives an answer-region-aware serialisation
(head, tail and answer rows of every sheet, values plus a formula overlay) and writes one
Python script that opens the real workbook, computes, and writes plain values into the
graded region. Script runs in a scratch directory; stderr feeds a bounded repair loop (2);
mechanical hygiene checks catch formula strings; a verification call reviews the written
region; a direct JSON fallback runs only if the code path produced nothing. Smoke on the
same 2 baseline tasks, then dev16 (`experiments/dev16-a1-001`, concurrency 6).

**Observations.** Smoke: both PASS, including 13-1's date cells (scripts write real
datetimes). Dev16: **14/16 (87.5%), cell_accuracy 0.9865**, cell-level 8/8, sheet-level 6/8;
34 model calls, 207k output tokens, ~24 min, ~$1.29. The two baseline truncation failures
(57232, 183-8) now pass — scripts don't enumerate cells. Both remaining failures were
near-misses: 230-16 wrote text values with trailing whitespace (7/12); 156-14 left two
cells empty (154/156).

**Next steps.** Two targeted fixes, each validated on the exact task it addresses:
a whitespace hygiene check, and a verifier that can see what changed.

## 4. Targeted fixes and confirmation — Sat night

**Steps.** Added a strip-whitespace value rule plus a mechanical check that routes padded
text into the repair loop; made the verifier list EMPTY cells explicitly and show the
answer region BEFORE (init) and AFTER (output) side by side; kept produced outputs over
the fallback; missing answer sheets are created by name rather than writing to the active
sheet. Re-ran the two failed tasks (`fix-check-001`, `fix-check-002`), then the whole
dev16 with the final config (`dev16-a1-002`).

**Observations.** 156-14: PASS 156/156 (the EMPTY-cell surfacing caught it). 230-16 first
*regressed* to 2/12 via a differently-sampled script that shifted the region one row —
which is precisely what the before/after comparison was built for; with it, 230-16 PASS
12/12 first attempt. Final-config dev16: **15/16 (93.75%), cell_accuracy 0.971**; the sole
miss (183-8) had passed in the previous run — temperature-0 sampling wobble, same as the
baseline exhibits. Every dev16 task passed with the final config in at least one run.
A full review of the branch also surfaced 15 verified findings (forbidden-model defaults
in starter docs, env/doc bugs, grader quirks such as noon-datetime rounding and an
inconsistent cell_accuracy denominator); doc-level items were fixed, and the affected
internal planning files were later removed in cleanup.

**Next steps.** Freeze the solver config. Verify the Docker judge contract, then decide as
a team when to spend the credits on the full 400.

## 5. Docker and submission prep — Sun 01:00–01:35

**Steps.** Built the container and ran it exactly per the judge contract (`/data`
read-only, empty `/out`, keys via env) on two tasks. Hardened the image: CPU-only torch
wheel index and the Qwen3.8 tokenizer baked at build time. Wrote `scripts/finalize.sh`
(score with `--all`, copy artifacts to root, grep traces for `golden`) and
`scripts/analyse_run.py` (per-task calls/tokens/time, failure buckets).

**Observations.** Both tasks PASS through the container; traces carry every required field;
no `golden` string in any prompt or trace. Image size 9.75 GB → 2.06 GB. Cost profile: a
1-cell task spent 17,929 output tokens (366 s) in its code call at the default (xhigh)
reasoning effort — reasoning effort is the dominant time lever.

**Next steps.** Launch the full 400 overnight — starting late enough that the shared
Tinker pool is quiet, early enough to leave scoring margin.

## 6. The full-400 run — Sun 00:39–03:50 (submitted artifacts)

**Steps.** Launched at concurrency 16. The run ultimately executed in four segments,
merged last-wins on non-ok status; completed answers were never re-rolled. Scored with the
shipped evaluator, `--all`, recalculation on.

**Observations.**
- Segment 1 (253/400, then killed externally): throughput reached 470→820 tok/s aggregate —
  the assumed ~140 tok/s cap was wrong; throughput scales with concurrency and off-peak
  hours. 17 errors, dominated by context-window overflows on giant workbooks: Tinker serves
  the model with a **64k context**, not the 1M a public listing suggested.
- Mid-run fix (commit `a76d3a5`, solver prompts unchanged for normal tasks): clamp
  max_tokens to the measured window, shrink the serialisation on overflow
  (120k→45k→16k chars), route no-code-block replies through the repair nudge.
- Segments 2–3: two external process kills traced to the local task supervisor (machine
  never slept; not OOM). Lesson: long paid runs must be nohup-detached. Segment 4
  (detached, concurrency 16) finished 144 tasks without interruption; the former overflow
  errors (80-42, 209-30, 455-35, 41-47…) passed with the fix.
- **Final: pass_rate 0.870 (348/400), cell_accuracy 0.9729, cell-level 0.9091, sheet-level
  0.784. items 400, missing 0.** 2/400 produced no answer (118-50, 42216 — the model
  exhausts its budget thinking about 5000-row ranges before emitting code; init copies
  stand in, status honest). Night's spend ~7.6M output tokens, ≈$45.

**Next steps.** Morning: failure analysis of the 52 fails; a fine-tuning experiment if the
arithmetic allows; a generalisation check on tasks outside the Verified 400.

## 7. LoRA SFT experiment — Sun 04:40–06:00 (not used at inference)

**Steps.** RL was ruled out by arithmetic (one GRPO step ≈ 8M thinking tokens, ~18 h at
the shared rate). Instead: rejection-sampling SFT on the harness's own verified outputs,
trained to emit the script with an empty think block. `scripts/build_sft.py` rebuilt the
exact inference prompt for every task that passed the 400 run and is outside the 78
stratified held-out ids: 258 examples, 665k tokens, 10 hand-audited (all read the
workbook; none hard-code answers; golden files used only to *select* examples —
disclosed). Trained LoRA rank 32, lr 2e-4, 2 epochs = 16 steps (~$6); evaluated the
checkpoint through the same harness on the 78 held-out tasks (`heldout78-sft-001`).

**Observations.** Fine-tuned: **52/78** vs base **68/78** — but at **1,313 vs 18,104
output tokens/task (14×) and 50 vs 335 s/task (7×)**. The fine-tune keeps the code style
and speed but loses the reasoning that decides *what* to compute: failures are
interpretation errors, 20 of 26 partial. Side effect: verify/repair share the no-think
model, so the verifier weakened too (passed 12 of the 26 failing outputs). Won 2 tasks the
base missed, lost 18. Final train NLL 0.205; checkpoint (TTL cleared)
`tinker://17741918-b3a7-5ae6-bf92-9556e1033720:train:0/sampler_weights/final`.

**Next steps (not attempted, out of time).** Cascade: fine-tuned model first, base model
when the verifier rejects; keep the base model for the verify phase; SFT targets that
retain a short thinking trace.

## 8. Failure taxonomy of the 52 fails — Sun morning

**Steps.** Classified every failed task from `results.json` and its trace; re-ran the two
no-answer errors under the disclosed errored-id policy after widening the retry token
budget to 45k (`error-retry-001`; commit `46fb92d`, declared in SUBMISSION.md).

**Observations.** 20 near-miss (≥90% cells right), 20 partial, 12 zero-correct.
- The strip-whitespace rule cuts both ways: some goldens keep source padding
  (290-27 `'GG '`, 341-40 `' Sales'`) — we strip and lose those cells, while the same rule
  won 230-16 on dev16.
- Some goldens store dates as *text* (269-43 `'2022/01/26'`) — the exact inverse of the
  baseline's dates-as-text failure.
- 41-47: 6395/6403 cells right, missing 8 'TOTAL' label rows. Across the 400: 7 fails
  trace to whitespace-strip, 4 to text-date conversion, 18 to empty header/label cells.
- The two no-answer tasks still fail at 45k tokens (118-50 never emits code; 42216's
  script arrives truncated mid-line): a genuine capability edge of the 27B, not a budget
  problem. Submitted artifacts unchanged; the wider budget stays in the code. 118-50's
  graded region is ~10k cells of which only 22 differ from the init workbook — one reason
  cell_accuracy sits far above pass_rate.

**Next steps.** Draft value-rule refinements (below) and check generalisation before
touching anything else.

## 9. ext40 generalisation check — Sun 03:00–05:09

**Steps.** Built `experiments/ext40`: 40 unseen tasks sampled (seed 1) from the original
SpreadsheetBench 912 pool (CC BY-SA 4.0) that are not in the Verified 400 —
512 candidates filtered to 353 eligible, 10 per bucket, renamed to the Verified layout,
oracle 1.0 on 40/40. Ran the submitted harness on it (`ext40-base-001`, ~$6.5).

**Observations.** **26/40 (65%), cell_accuracy 0.863** vs 87% on the Verified 400. Of the
14 fails: 2 whitespace-strip, 1 case-sensitivity, 1 harness error, ~2–3 look like golden
quirks of the unverified pool; the rest are genuinely wrong values, concentrated in
cell-level formula tasks (lookups, conditional sums). Honest read: **~12–15 points of real
generalisation gap** beyond self-inflicted rules and label noise. Run-to-run variance
~3–4 tasks per 40. Caveat: the leftover pool is unverified, so ext40 scores are best used
relatively, between configs.

**Next steps.** A `prompt-fixes` branch (copy-verbatim value rules, source-aware
whitespace check, medium-effort retry) recovers 19/52 of the 400's failures but is neutral
on ext40 (25 vs 26) — evidence it needs a proper two-run evaluation, so it is NOT merged
into the submission.

## 10. Final status — Sun 09:15

The submission is `main`: root `predictions.jsonl`, `outputs/`, `traces/`, `run.log`,
`results.json` are the full-400 run (0.870 / 0.9729). Model `Qwen/Qwen3.8-27B` via Tinker,
temperature 0, no fine-tune at inference. Docker image verified against the judge contract
(2.06 GB, tokenizer baked). The one post-run code change and the SFT experiment are both
declared in SUBMISSION.md. Credits: ~$55 (400 run) + ~$25 (dev/ext40/targeted) + ~$12
(SFT), well under the $1,000 budget.

## Future work

1. Merge `prompt-fixes` (copy-verbatim rules for moved values; whitespace/type rules only
   for newly computed ones) and evaluate with two full runs to beat sampling variance.
2. An exploration turn before script-writing for cell-level lookup tasks — the largest
   block of real ext40 failures.
3. Formula mode: write formulas and recalculate with LibreOffice inside the container,
   for tasks whose goldens preserve formula-produced text formats.
4. The SFT cascade: fine-tuned model first for its 14× token efficiency, base model as
   verifier and fallback — the experiment suggests speed and accuracy are separable.

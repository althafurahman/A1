# A1 lab notes

How we got from the 59% one-shot baseline to the submitted harness, stage by stage:
the approach at each point, what we found, and what we changed because of it. The runs
mentioned here are committed under `experiments/` and `research/submissions/`, each with
its `results.json`.

## 1. Trust the grader before trusting any score

Before calling a model we checked the measuring stick: the oracle evaluation (golden
against golden) scores a perfect 1.0 on all 400 tasks, and LibreOffice recalculation
returns correct values for formulas written without cached results. We also profiled the
dataset: a fifth of the workbooks are bigger than the text preview the starter baseline
shows the model, most answers span many cells, and a quarter of the workbooks have
multiple sheets. That profile ended up predicting most of what followed.

## 2. Reproduce the baseline and study how it fails

We ran the unchanged starter baseline on a stratified 16-task dev subset (four per bucket:
cell vs sheet tasks, small vs large answer ranges). It passed 10/16, with cell accuracy
barely over half. Reading the traces, the failures fell into clear buckets:

- **Truncation.** The model thinks at length, and either never finishes reasoning or runs
  out of budget while typing hundreds of answer cells as JSON.
- **Value typing.** Dates come back as text; goldens hold real datetimes.
- **Manipulation errors.** Sheet-level tasks end up shifted by a row, or with the wrong
  rows deleted.

The pattern told us the problem wasn't reasoning quality so much as the *format of the
answer*: forcing a model to re-emit a spreadsheet as text is the bottleneck.

## 3. Build a code-executing agent instead

Our harness has the model write a short Python script rather than the answer itself. The
model sees a serialisation of the workbook that always includes the answer region, the
head and tail of every sheet, and the formulas; the script opens the real workbook,
computes, and writes plain values into the graded cells. Failures feed back: script
errors return to the model for repair, mechanical checks reject formula strings, and a
verification step reviews what was written before we accept it. Only if the script path
produces nothing at all do we fall back to a direct JSON answer.

Same dev subset: 14/16, cell accuracy 0.99. Both baseline truncation failures now pass —
a script doesn't need to enumerate cells. The two remaining failures were near-misses:
one task written with trailing whitespace in text values, one with two cells left empty.

## 4. Fix exactly what the dev set exposed

Two targeted changes, each validated on the task that motivated it:

- A whitespace rule plus a mechanical check that sends padded text back for repair.
- A stronger verifier: it now lists empty cells explicitly and sees the answer region
  *before and after* the script ran, which is what finally catches row-shifted output.
  (We learned this the hard way — a re-run of the whitespace task produced clean values
  in the wrong rows, and the old verifier waved it through.)

Final config on the dev subset: 15/16. The one miss had passed in an earlier run;
sampling varies a little even at temperature zero, for the baseline as much as for us.

## 5. Package the way judges will run it

The pipeline executes model-written code, so it ships as a Docker container reading the
dataset read-only and writing all artifacts to an output mount. We trimmed the image to
about 2 GB (CPU-only torch, tokenizer baked in so start-up needs no external downloads)
and verified the exact judge command end to end: outputs, traces with every required
field, and no golden values anywhere in prompts or traces.

## 6. The full 400

The full run taught us two things mid-flight. First, the model is served with a 64k
context — far smaller than we had assumed — so the biggest workbooks overflowed; we
added a clamp and an adaptive serialisation that shrinks until the prompt fits. Second,
throughput scales with concurrency far better than our early measurements suggested, so
the run finished overnight rather than in the ten hours we had budgeted.

The run completed in segments (twice interrupted by our own machine, not the pipeline);
tasks that had errored were re-run after the context fix, and completed answers were
never re-rolled. Final, from the shipped evaluator over all 400 tasks:

**pass rate 0.870 — cell accuracy 0.9729 — cell-level 0.909, sheet-level 0.784**

Two tasks produced no answer at all: on huge answer ranges the model exhausts its token
budget reasoning before it ever emits code. We widened the retry budget afterwards and
they still fail — that is a genuine capability edge of this model, not a configuration
problem, and we left the artifacts honest rather than paper over it.

## 7. Fine-tuning: tried, measured, not used

We trained a LoRA on 258 of our own verified prompt-to-script pairs (held out 78
stratified tasks that were never trained on; goldens influenced only which examples were
*selected*, and that is disclosed). The result was a clean trade-off: the fine-tuned
model writes scripts with 14× fewer tokens and 7× faster, but passes 52/78 against the
base model's 68/78 — it keeps the style and loses the reasoning about *what* to compute.
It also weakens the verifier, which shares the model. We had agreed a gate in advance
(within two tasks of base) and it missed by a distance, so the submission uses the base
model. The checkpoint and training details are in SUBMISSION.md.

## 8. Where it still fails, honestly

Of the 52 failed tasks, twenty are near-misses with over 90% of cells correct. The
recurring causes taught us something about the benchmark as much as the harness:

- Our strip-whitespace rule wins some tasks and loses others — some goldens genuinely
  keep leading or trailing spaces copied from source data.
- Our dates-as-real-datetimes rule is usually right, but some goldens store dates as
  text: the exact inverse of the baseline's classic failure.
- A cluster of fails are empty header or label cells the script never wrote.

## 9. Does it generalise?

We built a 40-task set from the original SpreadsheetBench pool (tasks outside the
Verified 400) and ran the submitted harness on it: 26/40, against 87% on the Verified
set. Discounting the whitespace/text-date self-inflictions and a few label-noise cases in
that unverified pool, we estimate a real generalisation gap of roughly 12–15 points,
concentrated in cell-level lookup and conditional-sum tasks. That number is in the repo
because knowing where the harness is weak matters more than pretending it isn't.

## Submitted state

The repo root holds the full-400 artifacts (`predictions.jsonl`, `outputs/`, `traces/`,
`run.log`, `results.json` at 0.870 / 0.9729), the harness in `a1/`, and the verified
Dockerfile. Model: Qwen3.8-27B via Tinker, temperature 0, no fine-tune at inference. One
post-run code change (the wider retry budget) is declared in SUBMISSION.md alongside the
run's commit. Total spend stayed well under a tenth of the credit budget.

## Future improvements

1. **Copy-verbatim value rules.** Values moved or copied from existing cells should be
   copied exactly (type and whitespace); typing rules should apply only to newly computed
   values. A draft branch recovers a third of the current failures on the 400 but is
   neutral on the generalisation set — it needs a proper two-run evaluation before
   merging, so it stayed out of the submission.
2. **An exploration turn for lookup tasks.** Let the model inspect the workbook and probe
   its structure before writing the final script — the biggest block of real
   generalisation failures.
3. **Formula mode.** Write formulas and recalculate inside the container for tasks whose
   goldens preserve formula-produced text formats.
4. **The fine-tune cascade.** Use the 14×-cheaper fine-tuned model first and escalate to
   the base model when the verifier rejects — the experiment suggests speed and accuracy
   are separable rather than opposed.

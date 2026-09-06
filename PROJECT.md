# A1

A1 means the first cell of a spreadsheet.

## Goal and deliverable

Build a Python AI system that receives an Excel workbook and a written instruction, uses the permitted Qwen model, and returns the completed workbook. Submit a reproducible system that works unattended on unseen tasks. Priority: winning through task accuracy and reliability; secondary: a commercially useful spreadsheet capability; learning through controlled experiments.

Success is a valid judge-run submission, strong measured task pass rate, then cell accuracy, with a defensible method. No target score or improvement is promised before measurement.

## Sources and authority

- Starter: https://github.com/ylookup/encode-hackathon
- Reviewed starter commit: 37d9016264762a25cae49e077cd0893055bd9093
- Rules: research/SUBMISSION.md and research/SUBMISSION_TEMPLATE.md in the starter.
- Local briefing: ../YlookupEncodeHackathon.pdf (outside the team repository).
- Latest organiser message supplied by user: each team creates a Tinker project, receives $1,000 credits, and is strictly restricted to Qwen3.8-27B.

The latest model restriction overrides incompatible starter examples (DeepSeek and Qwen3-8B). Confirm exact API identifier; do not infer it from the display name. Record changes to rules if organisers clarify them.

## Components

- GitHub: code, instructions, experiment evidence and final submission.
- Python runner: reads tasks, contacts Qwen, manages operations, saves files and traces.
- Solver prompt: instructions loaded by Python and sent to Qwen; distinct from development instructions in AGENTS.md/CLAUDE.md.
- Tinker: remote model access and optional fine-tuning; project holds team access/credits.
- Google account: requested for organiser invitations; GCP hosting is not established as mandatory.
- Docker: required execution environment when running model-generated code.
- Official evaluator: compares completed workbooks to golden answers after LibreOffice recalculation.

## Baseline facts

400 tasks: 275 cell-level and 125 sheet-level. Every graded cell must match for a task to pass. The reported baseline is 59%, not locally reproduced. The starter sends a limited text preview (120 rows, 30 columns per sheet), requests final cell values, and writes them into a workbook. Its Tinker path has no explicit repair loop. Fine-tuning is optional.

## Final submission

Public team repo URL submitted via organiser form before Sunday 6 September 2026, 12:00 Europe/London.

- Working code, dependencies and run instructions; Dockerfile for an agent executing model-written code.
- SUBMISSION.md based on organiser template: team, method paragraph (150–300 words), exact model/checkpoint, configuration and scores.
- predictions.jsonl, outputs/, traces/, run.log for all 400 tasks.
- results.json from the unchanged official evaluator with --all and recalculation.
- Runtime reads /data (read-only), writes /out, receives keys through environment variables.
- If fine-tuned: accessible checkpoint and required training details.

The judges' run determines ranking; self-reported scores establish run order. Research-specific video/slides requirements are not explicit; general schedule mentions video and live judging, so confirm format. Do not assume Product's 3–5-minute video rule applies.

## Scope now

Team repository: https://github.com/althafurahman/A1, cloned into A1/ inside the original workspace. Establish authorised model access, reproduce the starter baseline, then investigate failures. Do not build a UI or launch training at this stage. Existing README architecture is a proposal, not implemented behaviour.

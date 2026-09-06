# A1 — shared project instructions

Read PROJECT.md, BASELINE.md and MEMORY.md before working. These instructions apply throughout this project. CLAUDE.md points here so both assistants share the same requirements.

- Goal: deliver a reliable spreadsheet-solving system for the Research track; maximise judges' task pass rate on unseen workbooks, then cell accuracy. Commercial usefulness is secondary; learning accompanies measured experiments.
- Only the organiser-permitted Qwen3.8-27B may be used in the solver or experiments. Its exact API identifier is unconfirmed. Never use starter defaults, guess an identifier, or silently fall back to another model.
- Claude Code and Codex are user-authorised development tools. They are not solver backends. Do not use other models to solve benchmark tasks or generate training answers; training-data permissions require organiser clarification.
- Never expose API keys, commit .env files, or print credentials. Credentials come from environment variables.
- Reproduce and preserve the starter baseline before optimising. Keep the official evaluator unchanged. Record commit, configuration, task coverage and actual results; never invent scores.
- Solver inputs must exclude golden workbooks and evaluation answers. No task-ID answer lookups. Training use of golden data requires explicit organiser clarification.
- Model-generated code runs only inside Docker. Judge input is /data, read-only; output is /out. Never execute generated code on the host.
- Prefer existing starter helpers and simple Python functions. No UI, agent framework or fine-tuning until an observed need justifies it.
- Use unique experiment directories: the starter deletes existing outputs and traces when a run begins. Never overwrite previous evidence.
- Preserve other contributors' edits. Check git status before editing; coordinate file ownership in MEMORY.md. No destructive resets or unrelated rewrites.
- Keep required prediction/workbook/log records for every task, including failures. Final scores use the shipped evaluator with --all and recalculation.
- Update MEMORY.md after meaningful work with facts, evidence paths, unresolved questions and the next action. Explain domain terms in plain language.

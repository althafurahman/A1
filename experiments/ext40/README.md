# ext40: unseen generalisation set

40 tasks drawn from the original SpreadsheetBench release (`spreadsheetbench_912_v0.1`, KAKA22/SpreadsheetBench on Hugging Face, CC BY-SA 4.0) that are NOT among the Verified 400 we develop on. Built by `scripts/build_ext40.py` (seed 1): 20 cell-level + 20 sheet-level, half with <=15 answer cells, after filtering tasks whose golden fails to load, whose answer range is unchanged between input and golden, or whose instruction asks for formatting or volatile functions. Test case 1 only; files renamed to the Verified layout (`1_<id>_init.xlsx`, `1_<id>_golden.xlsx`, `prompt.txt` = instruction).

Caveat: these come from the unverified leftover pool (216 of the 912 were removed as ambiguous or broken, 296 dropped as too easy, per the Verified release notes), so scores here are relative between configurations, not absolute accuracy. Nobody on the team has looked at these tasks before the first evaluation.

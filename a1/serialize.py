"""Rich workbook serialization: values grid plus formula overlay, answer-region aware.

The one-shot baseline shows the model 120x30 of values per sheet. 80 of the 400 workbooks
are bigger than that, and formulas are invisible in a data_only load. This serializer
shows both layers and guarantees the answer region and the tail of each sheet are visible,
under an overall character budget.
"""

from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries

from .sbio import answer_ranges

MAX_COLS = 40
HEAD_ROWS = 100
TAIL_ROWS = 10
FULL_SHEET_ROWS = 150
MAX_FORMULAS_PER_SHEET = 250
CHAR_BUDGET = 120_000


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return str(v)


def _grid(ws_vals, rows, cols):
    header = "\t".join(["row"] + [get_column_letter(c) for c in range(1, cols + 1)])
    lines = [header]
    for r in rows:
        vals = [ws_vals.cell(row=r, column=c).value for c in range(1, cols + 1)]
        lines.append("\t".join([str(r)] + [_fmt(v) for v in vals]))
    return lines


def _row_windows(ws, answer_rows):
    """Which rows to render: head, tail, and the answer region with margin, merged."""
    max_row = ws.max_row or 1
    if max_row <= FULL_SHEET_ROWS:
        return list(range(1, max_row + 1)), False
    spans = [(1, HEAD_ROWS), (max_row - TAIL_ROWS + 1, max_row)]
    for r1, r2 in answer_rows:
        spans.append((max(1, r1 - 3), min(max_row, r2 + 3)))
    spans.sort()
    merged = [spans[0]]
    for s in spans[1:]:
        if s[0] <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], s[1]))
        else:
            merged.append(s)
    rows = [r for a, b in merged for r in range(a, b + 1)]
    return rows, True


def _answer_rows_by_sheet(task, wb):
    out = {}
    for sheet, rng in answer_ranges(task):
        ws = wb[sheet] if sheet and sheet in wb.sheetnames else wb.active
        try:
            _, r1, _, r2 = range_boundaries(rng)
        except Exception:
            continue
        r1 = r1 or 1
        r2 = r2 or min(ws.max_row, r1 + 400)
        out.setdefault(ws.title, []).append((r1, r2))
    return out


def serialize_workbook(wb_vals, wb_form, task):
    """wb_vals: data_only load. wb_form: normal load (formulas visible)."""
    answer_map = _answer_rows_by_sheet(task, wb_vals)
    parts = []
    for ws in wb_vals.worksheets:
        ws_form = wb_form[ws.title]
        cols = min(ws.max_column or 1, MAX_COLS)
        # widen if the answer region lives beyond the column cap
        for sheet, rng in answer_ranges(task):
            target = ws.title if (sheet and sheet in wb_vals.sheetnames) else wb_vals.active.title
            if target == ws.title:
                try:
                    _, _, c2, _ = range_boundaries(rng)
                    if c2:
                        cols = min(max(cols, c2), 60)
                except Exception:
                    pass
        rows, truncated = _row_windows(ws, answer_map.get(ws.title, []))
        note = " (TRUNCATED: head, tail and answer-region rows shown)" if truncated else ""
        lines = [f"### Sheet: {ws.title} — {ws.max_row}x{ws.max_column}{note}"]
        lines += _grid(ws, rows, cols)

        formulas = []
        row_set = set(rows)
        for row in ws_form.iter_rows(max_col=min(ws_form.max_column or 1, 60)):
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    if cell.row in row_set or not truncated:
                        formulas.append(f"{cell.coordinate} {cell.value}")
                        if len(formulas) > MAX_FORMULAS_PER_SHEET:
                            break
            if len(formulas) > MAX_FORMULAS_PER_SHEET:
                formulas.append("... (more formulas omitted)")
                break
        if formulas:
            lines.append("Formulas (cell, formula — grid above shows their cached values):")
            lines += formulas
        parts.append("\n".join(lines))
    text = "\n\n".join(parts)
    if len(text) > CHAR_BUDGET:
        text = text[:CHAR_BUDGET] + "\n... (serialization truncated at budget)"
    return text

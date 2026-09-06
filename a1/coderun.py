"""Execute model-written Python against a copy of the init workbook, in a scratch dir.

The script sees two predefined names, INIT and OUT. It must leave a workbook at OUT.
Inside the Docker submission this runs in the container; nothing touches the host.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PREAMBLE = 'INIT = "init.xlsx"\nOUT = "output.xlsx"\n'
OUTPUT_CAP = 4000


def extract_code(text: str) -> str | None:
    """Last fenced python block in the reply, else the last fenced block, else None."""
    blocks = re.findall(r"```(?:python|py)?\n(.*?)```", text, flags=re.S)
    return blocks[-1].strip() if blocks else None


def run_code(code: str, init_xlsx: str, out_xlsx: str, timeout: int = 120) -> dict:
    """Returns {ok, stdout, stderr}. On ok the produced workbook is copied to out_xlsx."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copy(init_xlsx, tmp / "init.xlsx")
        (tmp / "script.py").write_text(PREAMBLE + code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "script.py"], cwd=tmp,
                capture_output=True, text=True, timeout=timeout,
            )
            stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            stdout = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            return {"ok": False, "stdout": stdout[-OUTPUT_CAP:], "stderr": f"timeout after {timeout}s"}
        produced = tmp / "output.xlsx"
        if rc == 0 and produced.exists():
            shutil.copy(produced, out_xlsx)
            return {"ok": True, "stdout": stdout[-OUTPUT_CAP:], "stderr": stderr[-OUTPUT_CAP:]}
        err = stderr or f"exit code {rc}"
        if rc == 0 and not produced.exists():
            err = "script exited 0 but wrote no output.xlsx"
        return {"ok": False, "stdout": stdout[-OUTPUT_CAP:], "stderr": err[-OUTPUT_CAP:]}

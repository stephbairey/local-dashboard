from __future__ import annotations
import os, io, sys, time, traceback
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]   # ...\dashboard\python -> parents[1] == ...\dashboard
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = DATA_DIR / "dashboard.log"

_MAX_BYTES = 512 * 1024  # 512 KB

def _rotate_if_needed(path: Path) -> None:
    try:
        if path.exists() and path.stat().st_size > _MAX_BYTES:
            bak = path.with_suffix(path.suffix + ".1")
            if bak.exists():
                try: bak.unlink()
                except Exception: pass
            path.rename(bak)
    except Exception:
        pass

def log(level: str, message: str, *, mod: str = "", **fields):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    extra = " ".join(f'{k}="{str(v).replace("\"","\\\"")}"' for k,v in fields.items())
    line = f"{t} [{level}] {mod} {message} {extra}".rstrip() + "\n"
    try:
        _rotate_if_needed(LOG_PATH)
        with io.open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Never raise from logger
        pass

def info(msg: str, **kw):  log("INFO", msg, **kw)
def warn(msg: str, **kw):  log("WARN", msg, **kw)
def error(msg: str, **kw): log("ERROR", msg, **kw)

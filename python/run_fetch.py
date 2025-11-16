from __future__ import annotations
import sys, time, runpy, os
from pathlib import Path
from util.simplelog import info, error

def main():
    if len(sys.argv) < 2:
        print("Usage: run_fetch.py <script_path.py> [args...]")
        sys.exit(2)
    script_path = Path(sys.argv[1]).resolve()
    args = sys.argv[2:]
    mod = script_path.stem

    t0 = time.time()
    info("start", mod=mod, path=str(script_path), args=" ".join(args))
    try:
        # Execute the target script as if run directly
        cwd_before = os.getcwd()
        os.chdir(str(script_path.parent))
        old_argv = sys.argv[:]
        sys.argv = [str(script_path)] + args
        try:
            runpy.run_path(str(script_path), run_name="__main__")
        finally:
            sys.argv = old_argv
            os.chdir(cwd_before)
        dt = round((time.time() - t0)*1000)
        info("ok", mod=mod, ms=dt)
    except SystemExit as ex:
        dt = round((time.time() - t0)*1000)
        code = int(getattr(ex, "code", 0) or 0)
        if code == 0:
            info("ok", mod=mod, ms=dt)
        else:
            error("exit", mod=mod, code=code, ms=dt)
            sys.exit(code)
    except Exception as ex:
        dt = round((time.time() - t0)*1000)
        error("exception", mod=mod, ms=dt, err=repr(ex))
        # Best-effort print for interactive runs
        try:
            import traceback; traceback.print_exc()
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()

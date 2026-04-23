"""
Unified Job Application Pipeline

One runner that chains the three discovery-and-outreach stages together:

  1. Handshake Easy Apply     → 036_handshake_apply_pa.py
  2. CalCareers monitor       → 041_calcareers_monitor.py
  3. GMass contact list build → build_gmass_master.py  (+ optional sheet push)

Each stage runs as a subprocess so a failure in one does not abort the others;
a single run folder collects logs and a summary of what each stage produced.

Usage:
  python 042_unified_pipeline.py                        # full run
  python 042_unified_pipeline.py --dry-run              # forwards --dry-run to each stage
  python 042_unified_pipeline.py --skip handshake       # repeatable, names: handshake|calcareers|gmass
  python 042_unified_pipeline.py --only gmass           # run just the GMass stage
  python 042_unified_pipeline.py --handshake-max 5      # forwards --max-applies to Handshake
  python 042_unified_pipeline.py --calcareers-pages 2   # forwards --pages to CalCareers
"""

import argparse
import csv
import json
import logging
import os
import shlex
import subprocess
import sys
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── CLI ───────────────────────────────────────────────────────────────────────
STAGES = ("handshake", "calcareers", "gmass")

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--skip", action="append", default=[], choices=STAGES,
                    help="Stage(s) to skip (repeatable)")
parser.add_argument("--only", action="append", default=[], choices=STAGES,
                    help="Stage(s) to run exclusively (repeatable)")
parser.add_argument("--handshake-max", type=int, default=8,
                    help="Forward as --max-applies to Handshake (default 8)")
parser.add_argument("--calcareers-pages", type=int, default=3,
                    help="Forward as --pages to CalCareers (default 3)")
parser.add_argument("--gmass-push-sheet", action="store_true",
                    help="Push the GMass CSV to a dedicated Google Sheet tab")
args = parser.parse_args()

if args.only:
    stages_to_run = [s for s in STAGES if s in args.only and s not in args.skip]
else:
    stages_to_run = [s for s in STAGES if s not in args.skip]

# ── Run folder ────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PYTHON_BIN  = os.environ.get("PIPELINE_PYTHON", sys.executable)
RUN_ID      = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR     = os.path.join(SCRIPT_DIR, "runs", f"unified_{RUN_ID}")
os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(RUN_DIR, "pipeline.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("pipeline")


# ── Stage runner ──────────────────────────────────────────────────────────────
def run_stage(name: str, cmd: list[str]) -> dict:
    """Run a subprocess, tee its stdout/stderr into the run dir, return summary."""
    stage_log = os.path.join(RUN_DIR, f"{name}.log")
    log.info(f"── {name.upper()} ──")
    log.info(f"$ {' '.join(shlex.quote(c) for c in cmd)}")
    start = datetime.now()
    last_line = ""

    with open(stage_log, "w") as fp:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                cwd=SCRIPT_DIR, text=True, bufsize=1)
        assert proc.stdout is not None
        for line in proc.stdout:
            fp.write(line)
            fp.flush()
            if line.strip():
                last_line = line.rstrip()
                # Forward concise stage output. Stages emit a final
                # "<STAGE>_SUMMARY ..." line we always surface.
                if "_SUMMARY" in line or line.startswith(("[ERROR]", "Error:")):
                    log.info(f"  {line.rstrip()}")
        proc.wait()

    duration = (datetime.now() - start).total_seconds()
    ok = proc.returncode == 0
    log.info(f"{name}: exit={proc.returncode} duration={duration:.1f}s")
    return {
        "stage":       name,
        "returncode":  proc.returncode,
        "ok":          ok,
        "duration_s":  duration,
        "log":         stage_log,
        "last_line":   last_line,
    }


# ── Stage builders ────────────────────────────────────────────────────────────
def handshake_cmd() -> list[str]:
    cmd = [PYTHON_BIN, "036_handshake_apply_pa.py", "--max-applies", str(args.handshake_max)]
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def calcareers_cmd() -> list[str]:
    cmd = [PYTHON_BIN, "041_calcareers_monitor.py", "--pages", str(args.calcareers_pages)]
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def gmass_cmd() -> list[str]:
    cmd = [PYTHON_BIN, "build_gmass_master.py"]
    if args.gmass_push_sheet:
        cmd.append("--push-sheet")
    return cmd


STAGE_CMDS = {
    "handshake":  handshake_cmd,
    "calcareers": calcareers_cmd,
    "gmass":      gmass_cmd,
}


# ── Summary ───────────────────────────────────────────────────────────────────
def write_summary(results: list[dict]):
    summary_path = os.path.join(RUN_DIR, "summary.json")
    with open(summary_path, "w") as f:
        json.dump({
            "run_id":    RUN_ID,
            "dry_run":   args.dry_run,
            "stages":    results,
            "finished":  datetime.now().isoformat(),
        }, f, indent=2)

    log.info("")
    log.info("===== PIPELINE SUMMARY =====")
    for r in results:
        status = "OK " if r["ok"] else "FAIL"
        log.info(f"  {status}  {r['stage']:<11} {r['duration_s']:>6.1f}s  {r['last_line']}")
    log.info(f"  run dir: {RUN_DIR}")
    log.info("============================")


def main() -> int:
    log.info(f"unified pipeline start run_id={RUN_ID} stages={stages_to_run} dry_run={args.dry_run}")
    if not stages_to_run:
        log.warning("no stages to run; exiting")
        return 0

    results: list[dict] = []
    for stage in stages_to_run:
        cmd = STAGE_CMDS[stage]()
        try:
            results.append(run_stage(stage, cmd))
        except FileNotFoundError as e:
            log.error(f"{stage}: script not found — {e}")
            results.append({"stage": stage, "returncode": 127, "ok": False,
                            "duration_s": 0, "log": "", "last_line": str(e)})

    write_summary(results)
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

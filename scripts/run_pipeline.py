#!/usr/bin/env python3
"""run_pipeline.py — single-command end-to-end runner for "Breaking Law".

Stages, in order (skip individually with --skip-<stage>):

  1. label-stills    — vision-label any unlabeled stills (writes .content.json)
  2. selects-tagger  — re-tag clips/images, drop quarantined-by-sidecar
  3. paper-edit      — director picks visuals beat-by-beat → paper_edit_v<N>.json
  4. render          — ffmpeg_production_render.py → output/breaking_law_*.mp4

Each stage runs sequentially. If a stage fails the pipeline halts and the
specific command + log path are printed so you can re-run that stage alone.

Usage:
  venv/bin/python scripts/run_pipeline.py
  venv/bin/python scripts/run_pipeline.py --version v12 --preview
  venv/bin/python scripts/run_pipeline.py --skip-label-stills --skip-selects
  venv/bin/python scripts/run_pipeline.py --only render --paper-edit storyboards/breaking_law_paper_edit_v11.json
"""

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(PROJECT_ROOT / "venv" / "bin" / "python")

STAGES = ["label-stills", "selects-tagger", "paper-edit", "render"]


def run(label: str, cmd: list[str], log_path: Path) -> int:
    """Run a stage. Stream output to terminal and tee to log_path."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n━━━ {label} ━━━")
    print(f"  cmd: {' '.join(shlex.quote(c) for c in cmd)}")
    print(f"  log: {log_path}")
    t0 = time.time()
    with open(log_path, "w") as logf:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1, cwd=str(PROJECT_ROOT))
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            logf.write(line)
        rc = proc.wait()
    dt = time.time() - t0
    print(f"  ── exit {rc} in {dt:.1f}s")
    return rc


def stage_label_stills(args, log_dir: Path) -> int:
    cmd = [PYTHON, "scripts/label_stills.py"]
    if args.force_label:
        cmd.append("--force")
    return run("label-stills", cmd, log_dir / "01_label_stills.log")


def stage_selects(args, log_dir: Path) -> int:
    cmd = [PYTHON, "-m", "pipeline_v2.selects_tagger"]
    return run("selects-tagger", cmd, log_dir / "02_selects.log")


def stage_paper_edit(args, log_dir: Path) -> int:
    out_json = PROJECT_ROOT / "storyboards" / f"breaking_law_paper_edit_{args.version}.json"
    out_md = PROJECT_ROOT / "storyboards" / f"breaking_law_paper_edit_{args.version}.md"
    cmd = [PYTHON, "-m", "pipeline_v2.paper_edit_generator",
           "--output-json", str(out_json),
           "--output-md", str(out_md)]
    rc = run("paper-edit", cmd, log_dir / "03_paper_edit.log")
    if rc == 0:
        print(f"  → wrote {out_json.name}")
    return rc


def stage_render(args, log_dir: Path) -> int:
    pe = args.paper_edit or str(PROJECT_ROOT / "storyboards" / f"breaking_law_paper_edit_{args.version}.json")
    if not Path(pe).exists():
        print(f"  ERROR: paper edit not found: {pe}")
        return 2
    out_name = f"breaking_law_{args.version}{'_preview' if args.preview else ''}.mp4"
    out_path = PROJECT_ROOT / "output" / out_name
    cmd = [PYTHON, "scripts/ffmpeg_production_render.py",
           "--paper-edit", pe,
           "--output", str(out_path)]
    if args.preview:
        cmd.append("--preview")
    return run("render", cmd, log_dir / "04_render.log")


STAGE_FUNCS = {
    "label-stills":   stage_label_stills,
    "selects-tagger": stage_selects,
    "paper-edit":     stage_paper_edit,
    "render":         stage_render,
}


def main():
    p = argparse.ArgumentParser(description="Pipeline runner for Breaking Law")
    p.add_argument("--version", default=time.strftime("v%y%m%d_%H%M%S"),
                   help="Version tag for output paper edit + render (default: timestamped)")
    p.add_argument("--preview", action="store_true", help="540p fast render")
    p.add_argument("--paper-edit", help="Override paper-edit path passed to render stage")
    p.add_argument("--force-label", action="store_true",
                   help="Re-label every still even if sidecar exists")
    p.add_argument("--only", choices=STAGES, action="append", default=[],
                   help="Run only these stages (repeatable)")
    for s in STAGES:
        p.add_argument(f"--skip-{s}", action="store_true", help=f"Skip the {s} stage")
    args = p.parse_args()

    to_run = args.only if args.only else STAGES
    to_run = [s for s in to_run if not getattr(args, f"skip_{s.replace('-','_')}")]

    log_dir = PROJECT_ROOT / "output" / "pipeline_logs" / args.version
    print(f"Pipeline run · version={args.version} · stages={to_run}")
    print(f"Logs: {log_dir}")

    for s in to_run:
        rc = STAGE_FUNCS[s](args, log_dir)
        if rc != 0:
            print(f"\n❌ Stage '{s}' failed (rc={rc}). Halting.")
            print(f"   See: {log_dir}")
            sys.exit(rc)

    print(f"\n✅ Pipeline complete. Logs in {log_dir}")


if __name__ == "__main__":
    main()

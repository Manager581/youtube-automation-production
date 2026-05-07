#!/usr/bin/env python3
"""run_pipeline.py — single-command end-to-end runner for any video project.

Stages, in order (skip individually with --skip-<stage>):

  1. label-stills    — vision-label any unlabeled stills (writes .content.json)
  2. selects-tagger  — re-tag clips/images, drop quarantined-by-sidecar
  3. paper-edit      — director picks visuals beat-by-beat → paper_edit_v<N>.json
  4. realign         — WhisperX wav2vec2 forced alignment of paper-edit timestamps
  5. silence-insert  — insert narration silence at every clip-audio beat
  6. render          — ffmpeg_production_render.py → output/<video>_<version>.mp4
  7. verify          — non-skippable; gates pipeline on critical failures

Per-video paths are derived from --video <name> (default: breaking_law) and
--script-version <ver> (default: v45). Each path can still be overridden
explicitly via --narration, --script, --alignment, --paper-edit, etc.

Usage:
  venv/bin/python scripts/run_pipeline.py
  venv/bin/python scripts/run_pipeline.py --version v12 --preview
  venv/bin/python scripts/run_pipeline.py --video frank_olson --script-version v3 --version v1 --preview
  venv/bin/python scripts/run_pipeline.py --only render --paper-edit storyboards/breaking_law_paper_edit_v11.json
"""

import argparse
import shlex
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(PROJECT_ROOT / "venv" / "bin" / "python")

STAGES = ["label-stills", "selects-tagger", "paper-edit", "realign",
          "silence-insert", "render", "verify"]


def derive_paths(video: str, script_version: str) -> dict:
    """Per-video default paths, used unless overridden by explicit CLI flags."""
    audio_dir = PROJECT_ROOT / "audio" / video
    storyboards = PROJECT_ROOT / "storyboards"
    return {
        "narration":            audio_dir / "narration.wav",
        "script_raw":           PROJECT_ROOT / "scripts" / f"raw_{video}_{script_version}.txt",
        "script_enhanced":      PROJECT_ROOT / "scripts" / f"enhanced_{video}_{script_version}.txt",
        "alignment_legacy":     audio_dir / "narration_alignment.json",
        "alignment_whisperx":   audio_dir / "narration_alignment_whisperx.json",
        "padded_narration":     audio_dir / "narration_padded.wav",
        "padded_alignment":     audio_dir / "narration_alignment_padded.json",
        "selects":              storyboards / f"{video}_selects.json",
        "paper_edit_basename":  f"{video}_paper_edit",
        "render_basename":      video,
    }


def run(label: str, cmd: list[str], log_path: Path) -> int:
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


def paper_edit_path(args) -> Path:
    """Canonical paper edit path for current run."""
    if args.paper_edit:
        return Path(args.paper_edit)
    return PROJECT_ROOT / "storyboards" / f"{args._paths['paper_edit_basename']}_{args.version}.json"


def render_path(args) -> Path:
    name = f"{args._paths['render_basename']}_{args.version}{'_preview' if args.preview else ''}.mp4"
    return PROJECT_ROOT / "output" / name


def stage_label_stills(args, log_dir: Path) -> int:
    cmd = [PYTHON, "scripts/label_stills.py"]
    if args.force_label:
        cmd.append("--force")
    return run("label-stills", cmd, log_dir / "01_label_stills.log")


def stage_selects(args, log_dir: Path) -> int:
    cmd = [PYTHON, "-m", "pipeline_v2.selects_tagger"]
    return run("selects-tagger", cmd, log_dir / "02_selects.log")


def stage_paper_edit(args, log_dir: Path) -> int:
    out_json = paper_edit_path(args)
    out_md = out_json.with_suffix(".md")
    paths = args._paths

    cmd = [PYTHON, "-m", "pipeline_v2.paper_edit_generator",
           "--output-json", str(out_json),
           "--output-md", str(out_md)]
    # Pass per-video overrides if the corresponding files exist
    if paths["script_enhanced"].exists():
        cmd.extend(["--script", str(paths["script_enhanced"])])
    if paths["alignment_legacy"].exists():
        cmd.extend(["--alignment", str(paths["alignment_legacy"])])
    if paths["selects"].exists():
        cmd.extend(["--selects", str(paths["selects"])])

    rc = run("paper-edit", cmd, log_dir / "03_paper_edit.log")
    if rc == 0:
        print(f"  → wrote {out_json.name}")
    return rc


def stage_realign(args, log_dir: Path) -> int:
    """WhisperX forced alignment. Cached if --alignment exists, otherwise computed."""
    pe = paper_edit_path(args)
    if not pe.exists():
        print(f"  ERROR: paper edit not found: {pe}")
        return 2

    align_path = Path(args.alignment) if args.alignment else args._paths["alignment_whisperx"]
    cmd = [PYTHON, "scripts/realign_paper_edit.py",
           "--paper-edit", str(pe),
           "--output", str(pe)]  # in-place

    if align_path.exists():
        cmd.extend(["--alignment", str(align_path)])
    else:
        narration = Path(args.narration) if args.narration else args._paths["narration"]
        # realign requires the RAW script (with [BEAT]/[CHAPTER:] markers it strips)
        script = Path(args.script) if args.script else args._paths["script_raw"]
        if not narration.exists() or not script.exists():
            print(f"  ERROR: cannot run forced alignment — missing narration or script")
            print(f"    narration: {narration} ({'OK' if narration.exists() else 'MISSING'})")
            print(f"    script:    {script} ({'OK' if script.exists() else 'MISSING'})")
            return 2
        cmd.extend(["--narration", str(narration), "--script", str(script)])

    return run("realign", cmd, log_dir / "03b_realign.log")


def stage_silence_insert(args, log_dir: Path) -> int:
    """Insert narration silence at every clip-audio beat."""
    pe = paper_edit_path(args)
    if not pe.exists():
        print(f"  ERROR: paper edit not found: {pe}")
        return 2

    align = Path(args.alignment) if args.alignment else args._paths["alignment_whisperx"]
    if not align.exists():
        print(f"  ERROR: alignment not found: {align} (run realign stage first)")
        return 2

    narration = Path(args.narration) if args.narration else args._paths["narration"]
    if not narration.exists():
        print(f"  ERROR: narration not found: {narration}")
        return 2

    out_align = Path(args.padded_alignment) if args.padded_alignment else args._paths["padded_alignment"]
    out_narration = Path(args.padded_narration) if args.padded_narration else args._paths["padded_narration"]

    cmd = [PYTHON, "-m", "pipeline_v2.silence_inserter",
           "--paper-edit", str(pe),
           "--alignment", str(align),
           "--narration", str(narration),
           "--out-paper-edit", str(pe),  # in-place
           "--out-alignment", str(out_align),
           "--out-narration", str(out_narration)]
    return run("silence-insert", cmd, log_dir / "03c_silence_insert.log")


def stage_render(args, log_dir: Path) -> int:
    pe = paper_edit_path(args)
    if not pe.exists():
        print(f"  ERROR: paper edit not found: {pe}")
        return 2
    out_path = render_path(args)

    padded_narration = Path(args.padded_narration) if args.padded_narration else args._paths["padded_narration"]
    cmd = [PYTHON, "scripts/ffmpeg_production_render.py",
           "--paper-edit", str(pe),
           "--output", str(out_path)]
    if padded_narration.exists():
        cmd.extend(["--narration", str(padded_narration)])
    elif args.narration:
        cmd.extend(["--narration", args.narration])
    if args.preview:
        cmd.append("--preview")
    return run("render", cmd, log_dir / "04_render.log")


def stage_verify(args, log_dir: Path) -> int:
    pe = paper_edit_path(args)
    rp = render_path(args)
    if not rp.exists():
        print(f"  ERROR: render not found: {rp}")
        return 2
    report_path = log_dir / "verify_report.json"
    cmd = [PYTHON, "scripts/verify_render.py",
           "--render", str(rp),
           "--paper-edit", str(pe),
           "--report", str(report_path),
           "--skip-vision",
           "--fail-on-critical"]

    # Prefer padded alignment (silence-insert ran), fall back to whisperx, then explicit override
    padded_align = Path(args.padded_alignment) if args.padded_alignment else args._paths["padded_alignment"]
    whisperx_align = args._paths["alignment_whisperx"]
    if padded_align.exists():
        cmd.extend(["--alignment", str(padded_align)])
    elif whisperx_align.exists():
        cmd.extend(["--alignment", str(whisperx_align)])
    elif args.alignment:
        cmd.extend(["--alignment", args.alignment])
    return run("verify", cmd, log_dir / "05_verify.log")


STAGE_FUNCS = {
    "label-stills":    stage_label_stills,
    "selects-tagger":  stage_selects,
    "paper-edit":      stage_paper_edit,
    "realign":         stage_realign,
    "silence-insert":  stage_silence_insert,
    "render":          stage_render,
    "verify":          stage_verify,
}


def main():
    p = argparse.ArgumentParser(description="Pipeline runner for video projects")
    p.add_argument("--video", default="breaking_law",
                   help="Video project name (drives default paths). Default: breaking_law")
    p.add_argument("--script-version", default="v45",
                   help="Script version tag for default raw/enhanced script filenames. Default: v45")
    p.add_argument("--version", default=time.strftime("v%y%m%d_%H%M%S"),
                   help="Version tag for output paper edit + render (default: timestamped)")
    p.add_argument("--preview", action="store_true", help="540p fast render")
    p.add_argument("--paper-edit", help="Override paper-edit path")
    p.add_argument("--alignment", help="Override WhisperX-shaped alignment JSON path")
    p.add_argument("--narration", help="Override narration WAV path")
    p.add_argument("--script", help="Override script path (raw, with markers — for realign)")
    p.add_argument("--padded-narration", help="Override output padded narration WAV path")
    p.add_argument("--padded-alignment", help="Override output padded alignment JSON path")
    p.add_argument("--force-label", action="store_true",
                   help="Re-label every still even if sidecar exists")
    p.add_argument("--only", choices=STAGES, action="append", default=[],
                   help="Run only these stages (repeatable)")
    for s in STAGES:
        if s == "verify":
            continue  # verify is non-skippable
        p.add_argument(f"--skip-{s}", action="store_true", help=f"Skip the {s} stage")
    args = p.parse_args()

    args._paths = derive_paths(args.video, args.script_version)

    to_run = args.only if args.only else STAGES
    to_run = [s for s in to_run if not getattr(args, f"skip_{s.replace('-','_')}", False)]

    log_dir = PROJECT_ROOT / "output" / "pipeline_logs" / f"{args.video}_{args.version}"
    print(f"Pipeline · video={args.video} · script={args.script_version} · "
          f"version={args.version} · stages={to_run}")
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

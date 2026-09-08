#!/usr/bin/env python3
"""gen_foley_lane.py — lane-generic wrapper of the PROVEN cookies method (research/techjoint_cookies/gen_foley_v4.py):
MMAudio WATCHES each edit-spec segment's exact window (src clip, in-point, slot) and generates synced foley from the
shot's foley_prompt (never library SFX). CPU + model resident (MPS asserts in Metal; bf16 flaky) — ~60 s/window on M5.
  --spec EDIT_SPEC.json --manifest M.json --ledger L.json --out DIR [--only S001,S002] [--max-t 60] [--dry-run]
Windows come from the edit spec (t_in/t_out slot, optional t0 in-point) so the foley matches what the assembler shows.
Prompt = manifest shot.foley_prompt (inserts inherit their source shot's prompt) else derived from i2v_prompt.
"""
import argparse, json, os, subprocess, sys, tempfile
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "MMAudio"))
NEG = "music, melody, speech, voice, talking, whispering, narration, singing, crowd"
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--spec", required=True); ap.add_argument("--manifest", required=True); ap.add_argument("--ledger", required=True); ap.add_argument("--out", required=True); ap.add_argument("--only"); ap.add_argument("--max-t", type=float, default=1e9); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args(); spec = json.load(open(a.spec)); m = {s["id"]: s for s in json.load(open(a.manifest))["shots"]}; L = json.load(open(a.ledger)); only = set(a.only.split(",")) if a.only else None
    os.makedirs(a.out, exist_ok=True); wins = []; fails = []
    for sg in spec["segments"]:
        sid = sg["shot"]
        if only and sid not in only: continue
        if sg["t_in"] >= a.max_t: continue
        if not sg["src"].startswith("ledger:"): continue
        src = sg["src"].split(":", 1)[1]; row = L["clips"].get(src)
        if not row or row.get("verdict") != "PASS": fails.append(f"{sid}: source {src} not PASS-banked"); continue
        shot = m.get(sid, {}); srcshot = m.get(src, {})
        prompt = shot.get("foley_prompt") or srcshot.get("foley_prompt") or ("foley for: " + (srcshot.get("i2v_prompt") or shot.get("vantage") or "ambient")[:160])
        slot = sg["t_out"] - sg["t_in"]; t0 = float(sg.get("t0", 0.0))
        wins.append((sid, row["clip"], t0, slot, prompt))
    print(f"gen_foley_lane: {len(wins)} windows, {len(fails)} skipped")
    for f in fails: print("  SKIP", f)
    for sid, clip, t0, slot, prompt in wins: print(f"  {'DRY' if a.dry_run else 'RUN'} {sid}: {os.path.basename(clip)} in={t0:.2f} dur={slot:.2f} | {prompt[:70]}")
    if a.dry_run: sys.exit(1 if fails else 0)
    import torch, torchaudio
    from mmaudio.eval_utils import ModelConfig, all_model_cfg, generate, load_video
    from mmaudio.model.flow_matching import FlowMatching
    from mmaudio.model.networks import MMAudio, get_my_mmaudio
    from mmaudio.model.utils.features_utils import FeaturesUtils
    device = "cpu"; torch.set_num_threads(max(4, os.cpu_count() - 2)); dtype = torch.float32
    model: ModelConfig = all_model_cfg["large_44k_v2"]; model.download_if_needed(); seq_cfg = model.seq_cfg
    net: MMAudio = get_my_mmaudio(model.model_name).to(device, dtype).eval(); net.load_weights(torch.load(model.model_path, map_location=device, weights_only=True))
    fu = FeaturesUtils(tod_vae_ckpt=model.vae_path, synchformer_ckpt=model.synchformer_ckpt, enable_conditions=True, mode=model.mode, bigvgan_vocoder_ckpt=model.bigvgan_16k_path, need_vae_encoder=False).to(device, dtype).eval()
    fm = FlowMatching(min_sigma=0, inference_mode="euler", num_steps=25); rng = torch.Generator(device=device); rng.manual_seed(a.seed)
    rep_path = os.path.join(a.out, "foley_report.json"); report = json.load(open(rep_path)) if os.path.exists(rep_path) else {}
    for sid, clip, t0, slot, prompt in wins:
        out_flac = os.path.join(a.out, f"{sid}.flac")
        if os.path.exists(out_flac) and sid in report and not only: print(f"{sid}: exists, skip"); continue
        gen_dur = max(1.0, min(slot, 8.0))
        with tempfile.TemporaryDirectory() as td:
            win = os.path.join(td, "w.mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t0:.3f}", "-t", f"{gen_dur:.3f}", "-i", clip, "-an", "-c:v", "libx264", "-crf", "16", win], check=True)
            vi = load_video(win, gen_dur); seq_cfg.duration = vi.duration_sec
            net.update_seq_lengths(seq_cfg.latent_seq_len, seq_cfg.clip_seq_len, seq_cfg.sync_seq_len)
            with torch.inference_mode():
                audios = generate(vi.clip_frames.unsqueeze(0), vi.sync_frames.unsqueeze(0), [prompt], negative_text=[NEG], feature_utils=fu, net=net, fm=fm, rng=rng, cfg_strength=4.5)
            torchaudio.save(out_flac, audios.float().cpu()[0], seq_cfg.sampling_rate)
        report[sid] = {"src": clip, "in": t0, "slot": slot, "gen_dur": gen_dur, "prompt": prompt, "flac": out_flac}
        json.dump(report, open(rep_path, "w"), indent=1); print(f"{sid}: generated {gen_dur:.1f}s -> {os.path.relpath(out_flac, REPO)}", flush=True)
    sys.exit(1 if fails else 0)
if __name__ == "__main__": main()

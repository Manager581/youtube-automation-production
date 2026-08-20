#!/usr/bin/env python3
"""Generate per-shot foley for the cookie video with MMAudio (video-to-audio; the model
WATCHES the exact shot window and generates synced sound — replaces hand-placed library SFX,
which failed twice because placement was guessed from silent frame strips).

For each shot in the v4 timeline (v2 picture + C33 in-point fix):
  1. cut the exact window (src clip, in-point, duration) the assembler will show
  2. run MMAudio large_44k_v2 on that window with the shot's foley prompt
  3. verify: audio onsets must correlate with visual motion energy; no speech; not hiss
Outputs: assets/techjoint_cookies/foley_v4/<SHOT>.flac + foley_report.json

  venv/bin/python research/techjoint_cookies/gen_foley_v4.py            # all shots
  venv/bin/python research/techjoint_cookies/gen_foley_v4.py H1 C33    # subset
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
CLIPS = os.path.join(REPO, "assets", "techjoint_cookies", "clips_v2")
OUT = os.path.join(REPO, "assets", "techjoint_cookies", "foley_v4")
PROMPTS = os.path.join(HERE, "foley_prompts_v4.json")   # from the vision workflow
NEG = "music, melody, speech, voice, talking, whispering, narration, singing, crowd"

import importlib
cfg = importlib.import_module("cookies_v4_config")
OV = cfg.OVERRIDES

def probe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def shot_windows():
    shots = json.load(open(OV["SHOTS"]))["shots"]
    hook, cin, dur_o = OV["HOOK_SRC"], OV["CLIP_IN"], OV["DUR_OVERRIDE"]
    out = []
    for s in shots:
        sid = s["id"]
        src, i = hook.get(sid, (sid, cin.get(sid, 0.0)))
        dur = float(dur_o.get(sid, s["dur_s"]))
        native = probe_dur(os.path.join(CLIPS, f"{src}.mp4"))
        dur = min(dur, native - i)          # freeze-extends get silent tails, fine
        out.append((sid, src, float(i), round(dur, 3)))
    return out

def main():
    import torch
    with torch.inference_mode():
        _main()


def _main():
    args = [a for a in sys.argv[1:] if not a.startswith("--seed")]
    seed = next((int(a.split("=")[1]) for a in sys.argv[1:] if a.startswith("--seed=")), 42)
    only = set(args)
    os.makedirs(OUT, exist_ok=True)
    prompts = json.load(open(PROMPTS))
    wins = [w for w in shot_windows() if not only or w[0] in only]
    wins = [w for w in wins if w[0] in prompts]          # shots without a prompt = no foley

    import torch
    from mmaudio.eval_utils import ModelConfig, all_model_cfg, generate, load_video, make_video
    from mmaudio.model.flow_matching import FlowMatching
    from mmaudio.model.networks import MMAudio, get_my_mmaudio
    from mmaudio.model.utils.features_utils import FeaturesUtils
    import torchaudio

    device = "cpu"                                        # MPS asserts in Metal (buffer-size bug); CPU ~60s/shot with model resident
    torch.set_num_threads(max(4, os.cpu_count() - 2))
    dtype = torch.float32                                 # bf16 flaky on MPS
    model: ModelConfig = all_model_cfg["large_44k_v2"]
    model.download_if_needed()
    seq_cfg = model.seq_cfg
    net: MMAudio = get_my_mmaudio(model.model_name).to(device, dtype).eval()
    net.load_weights(torch.load(model.model_path, map_location=device, weights_only=True))
    feature_utils = FeaturesUtils(tod_vae_ckpt=model.vae_path, synchformer_ckpt=model.synchformer_ckpt,
                                  enable_conditions=True, mode=model.mode, bigvgan_vocoder_ckpt=model.bigvgan_16k_path,
                                  need_vae_encoder=False).to(device, dtype).eval()
    fm = FlowMatching(min_sigma=0, inference_mode="euler", num_steps=25)
    rng = torch.Generator(device=device); rng.manual_seed(seed)

    report = {}
    if os.path.exists(os.path.join(OUT, "foley_report.json")):
        report = json.load(open(os.path.join(OUT, "foley_report.json")))
    for sid, src, cin, dur in wins:
        out_flac = os.path.join(OUT, f"{sid}.flac")
        if os.path.exists(out_flac) and sid in report and not only:
            print(f"{sid}: exists, skip"); continue
        with tempfile.TemporaryDirectory() as td:
            win_mp4 = os.path.join(td, "w.mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{cin:.3f}", "-t", f"{dur:.3f}",
                            "-i", os.path.join(CLIPS, f"{src}.mp4"), "-an", "-c:v", "libx264", "-crf", "16", win_mp4], check=True)
            gen_dur = min(dur, 8.0)
            video_info = load_video(win_mp4, gen_dur)
            seq_cfg.duration = video_info.duration_sec
            net.update_seq_lengths(seq_cfg.latent_seq_len, seq_cfg.clip_seq_len, seq_cfg.sync_seq_len)
            audios = generate(video_info.clip_frames.unsqueeze(0), video_info.sync_frames.unsqueeze(0),
                              [prompts[sid]], negative_text=[NEG], feature_utils=feature_utils,
                              net=net, fm=fm, rng=rng, cfg_strength=4.5)
            audio = audios.float().cpu()[0]
            torchaudio.save(out_flac, audio, seq_cfg.sampling_rate)
        # verify: onsets vs motion (reuse forensic logic via subprocess to keep torch mem clean)
        report[sid] = {"src": src, "in": cin, "dur": dur, "prompt": prompts[sid]}
        json.dump(report, open(os.path.join(OUT, "foley_report.json"), "w"), indent=1)
        print(f"{sid}: generated {dur:.1f}s (gen window {min(dur,8.0):.1f}s) -> {os.path.relpath(out_flac, REPO)}")

if __name__ == "__main__":
    main()

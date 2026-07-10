#!/usr/bin/env python3
"""AMBER stage B — VACE-1.3B masked-crop generation on MPS, crash-proofed.

Two phases, run as SEPARATE processes (process exit is the only reliable way
to return memory on MPS):
  --phase encode    UMT5-XXL on CPU (swappable, machine-safe) -> embeds.pt, exit
  --phase generate  transformer bf16 + VAE fp32 on MPS, capped watermarks

Run with tools/ltx-video/ltx_env.nosync/bin/python.
"""
import gc
import json
import os
import sys
import time
from pathlib import Path

# Caps BEFORE torch import: hard shutdowns on this machine were PyTorch's
# default 1.7x watermark allowing ~27GB of wired GPU memory on a 24GB Mac.
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.9")
os.environ.setdefault("PYTORCH_MPS_LOW_WATERMARK_RATIO", "0.7")

import psutil
import torch

WORK = Path(__file__).resolve().parent / "work" / os.environ.get("AMBER_BEAT", "beat01_strike")
MODEL = "Wan-AI/Wan2.1-VACE-1.3B-diffusers"
NUM_STEPS = 20
GUIDANCE = 5.0
SEED = 42

meta = json.loads((WORK / "meta.json").read_text())
sheet = json.loads((WORK / "event_sheet.json").read_text())
MW = meta.get("model_w", meta.get("model_size"))
MH = meta.get("model_h", meta.get("model_size"))
NUM_FRAMES = meta["num_frames"]
NEG = "static, frozen, motionless, blurry, deformed, extra limbs, cartoon, low quality, watermark, text"


def preflight(min_gb):
    import re
    import subprocess
    avail = psutil.virtual_memory().available / 1e9
    # psutil undercounts reclaimable file cache on macOS; trust the kernel's
    # pressure view too (memory_pressure counts droppable cache as free).
    mp = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True).stdout
    m = re.search(r"free percentage: (\d+)", mp)
    free_pct = int(m.group(1)) if m else 0
    print(f"[preflight] psutil_avail={avail:.1f}GB kernel_free={free_pct}% "
          f"(need {min_gb}GB or >=30%)", flush=True)
    if avail < min_gb and free_pct < 30:
        sys.exit("ABORT: memory genuinely low — close apps and retry")


def phase_encode():
    preflight(6)  # CPU-side; swap keeps this safe even if tight
    from diffusers import WanVACEPipeline

    pipe = WanVACEPipeline.from_pretrained(
        MODEL, transformer=None, vae=None, torch_dtype=torch.bfloat16
    )
    t0 = time.time()
    with torch.no_grad():
        pos, neg = pipe.encode_prompt(
            prompt=sheet["prompt"], negative_prompt=NEG, device="cpu",
        )
    torch.save({"pos": pos.to(torch.bfloat16), "neg": neg.to(torch.bfloat16)},
               WORK / "embeds.pt")
    print(f"[encode] done in {time.time()-t0:.0f}s -> embeds.pt", flush=True)


def phase_generate():
    preflight(9)
    from diffusers import AutoencoderKLWan, WanVACEPipeline
    from diffusers.utils import export_to_video
    from PIL import Image

    # VAE stays on CPU in fp32: its 3D convs allocate ~10GB of MPSGraph
    # workspace OUTSIDE the PyTorch pool (both prior OOMs died there).
    # CPU memory is swappable = machine-safe; only the 1.3B DiT gets MPS.
    vae = AutoencoderKLWan.from_pretrained(MODEL, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanVACEPipeline.from_pretrained(
        MODEL, vae=vae, text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16
    )
    # UniPC is unstable on MPS ("rainbow noise" — documented Mac failure mode);
    # the community-standard fix is euler-family flow matching.
    from diffusers import FlowMatchEulerDiscreteScheduler
    shift = getattr(pipe.scheduler.config, "flow_shift", 3.0)
    pipe.scheduler = FlowMatchEulerDiscreteScheduler(shift=shift)
    print(f"[scheduler] FlowMatchEuler shift={shift}", flush=True)
    pipe.transformer.to("mps")

    from diffusers.models.autoencoders.vae import DiagonalGaussianDistribution
    from diffusers.models.modeling_outputs import AutoencoderKLOutput

    _enc, _dec = vae.encode, vae.decode

    def cpu_encode(x, return_dict=True):
        t0 = time.time()
        out = _enc(x.to("cpu", torch.float32), return_dict=True)
        dist = DiagonalGaussianDistribution(
            out.latent_dist.parameters.to("mps", torch.bfloat16)
        )
        print(f"[vae] cpu encode {tuple(x.shape)} in {time.time()-t0:.0f}s", flush=True)
        return AutoencoderKLOutput(latent_dist=dist) if return_dict else (dist,)

    def cpu_decode(z, return_dict=True, **kw):
        t0 = time.time()
        out = _dec(z.to("cpu", torch.float32), return_dict=return_dict, **kw)
        print(f"[vae] cpu decode in {time.time()-t0:.0f}s", flush=True)
        return out

    vae.encode, vae.decode = cpu_encode, cpu_decode
    gc.collect()

    emb = torch.load(WORK / "embeds.pt")
    pos = emb["pos"].to("mps", torch.bfloat16)
    neg = emb["neg"].to("mps", torch.bfloat16)

    crop = Image.open(WORK / "crop.png").convert("RGB")
    mask = Image.open(WORK / "mask.png").convert("L")
    video = [crop] * NUM_FRAMES
    masks = [mask] * NUM_FRAMES
    ref_path = WORK / "ref.png"
    refs = [Image.open(ref_path).convert("RGB")] if ref_path.exists() else None
    print(f"[ref] reference_images={'yes' if refs else 'no'}", flush=True)

    t0 = time.time()

    def on_step(p, i, t, kw):
        wired = torch.mps.driver_allocated_memory() / 1e9
        avail = psutil.virtual_memory().available / 1e9
        print(f"[step {i+1}/{NUM_STEPS}] {time.time()-t0:.0f}s "
              f"mps_driver={wired:.1f}GB sys_avail={avail:.1f}GB", flush=True)
        return kw

    out = pipe(
        video=video,
        mask=masks,
        reference_images=refs,
        prompt_embeds=pos,
        negative_prompt_embeds=neg,
        height=MH, width=MW, num_frames=NUM_FRAMES,
        num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE,
        generator=torch.Generator("cpu").manual_seed(SEED),
        callback_on_step_end=on_step,
    ).frames[0]

    gen_dir = WORK / "gen"
    gen_dir.mkdir(exist_ok=True)
    for i, fr in enumerate(out):
        Image.fromarray((fr * 255).astype("uint8") if hasattr(fr, "astype") else fr).save(
            gen_dir / f"{i:04d}.png"
        )
    export_to_video(out, str(WORK / "gen_preview.mp4"), fps=meta["fps"])
    peak = torch.mps.driver_allocated_memory() / 1e9
    print(f"[generate] DONE {time.time()-t0:.0f}s total, final mps_driver={peak:.1f}GB", flush=True)


if __name__ == "__main__":
    {"encode": phase_encode, "generate": phase_generate}[sys.argv[sys.argv.index("--phase") + 1]]()

#!/usr/bin/env python3
"""AMBER stage E — full-frame i2v with Wan2.2 TI2V-5B Turbo (4-step distilled, Q8 GGUF).

The replication attempt: Grok-style whole-scene choreography needs full-frame
generation — the masked-crop tier can't do traversal by construction. The 5B's
64x-compression VAE keeps full-frame token counts modest, Turbo's 4 steps at
CFG 1 mean a single denoising pass, and the GGUF transformer is 5.4GB.
Same crash-proofing: watermark caps, CPU VAE shim, UMT5 reused from the
VACE cache. Run with tools/ltx-video/ltx_env.nosync/bin/python.
"""
import gc
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.9")
os.environ.setdefault("PYTORCH_MPS_LOW_WATERMARK_RATIO", "0.7")

import psutil
import torch

WORK = Path(__file__).resolve().parent / "work" / os.environ.get("AMBER_BEAT", "beat04_turbo")
WORK.mkdir(parents=True, exist_ok=True)

GGUF = Path.home() / ".cache/huggingface/hub"  # resolved below via hf_hub_download cache
BASE = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
TE_REPO = "Wan-AI/Wan2.1-VACE-1.3B-diffusers"   # same UMT5-XXL, already cached
NUM_STEPS = 4
GUIDANCE = 1.0
SEED = int(os.environ.get("AMBER_SEED", "42"))
WIDTH, HEIGHT, NUM_FRAMES, FPS_OUT = 704, 416, 121, 20  # 121f @ 20fps = 6.05s

PROMPT = (
    "massive armored dunkleosteus turns toward the camera and swims directly "
    "at the viewer with powerful tail strokes, jaws gaping wide open filling "
    "the frame, then slams into the seabed kicking up an explosion of "
    "sediment, god rays shifting through the water, photorealistic underwater "
    "wildlife documentary footage"
)


def preflight(min_gb):
    import re
    import subprocess
    avail = psutil.virtual_memory().available / 1e9
    mp = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True).stdout
    m = re.search(r"free percentage: (\d+)", mp)
    free_pct = int(m.group(1)) if m else 0
    print(f"[preflight] psutil_avail={avail:.1f}GB kernel_free={free_pct}%", flush=True)
    if avail < min_gb and free_pct < 30:
        sys.exit("ABORT: memory genuinely low")


def main():
    preflight(8)
    from diffusers import (
        AutoencoderKLWan,
        FlowMatchEulerDiscreteScheduler,
        GGUFQuantizationConfig,
        WanImageToVideoPipeline,
        WanTransformer3DModel,
    )
    from huggingface_hub import hf_hub_download
    from PIL import Image

    gguf_path = hf_hub_download("hum-ma/Wan2.2-TI2V-5B-Turbo-GGUF",
                                "Wan2_2-TI2V-5B-Turbo-Q8_0.gguf")
    t0 = time.time()
    transformer = WanTransformer3DModel.from_single_file(
        gguf_path,
        quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
        config=BASE, subfolder="transformer", torch_dtype=torch.bfloat16,
    )
    vae = AutoencoderKLWan.from_pretrained(BASE, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanImageToVideoPipeline.from_pretrained(
        BASE, transformer=transformer, vae=vae,
        text_encoder=None, tokenizer=None, torch_dtype=torch.bfloat16,
    )
    pipe.scheduler = FlowMatchEulerDiscreteScheduler(shift=5.0)
    pipe.transformer.to("mps")
    print(f"[load] {time.time()-t0:.0f}s", flush=True)

    # CPU VAE shim (same rationale as stage B: MPSGraph 3D-conv workspace)
    from diffusers.models.autoencoders.vae import DiagonalGaussianDistribution
    from diffusers.models.modeling_outputs import AutoencoderKLOutput

    _enc, _dec = vae.encode, vae.decode

    def cpu_encode(x, return_dict=True):
        t = time.time()
        out = _enc(x.to("cpu", torch.float32), return_dict=True)
        dist = DiagonalGaussianDistribution(out.latent_dist.parameters.to("mps", torch.bfloat16))
        print(f"[vae] cpu encode {tuple(x.shape)} in {time.time()-t:.0f}s", flush=True)
        return AutoencoderKLOutput(latent_dist=dist) if return_dict else (dist,)

    def cpu_decode(z, return_dict=True, **kw):
        t = time.time()
        out = _dec(z.to("cpu", torch.float32), return_dict=return_dict, **kw)
        print(f"[vae] cpu decode in {time.time()-t:.0f}s", flush=True)
        return out

    vae.encode, vae.decode = cpu_encode, cpu_decode
    gc.collect()

    # Prompt embeds precomputed by stage_b --phase encode convention: reuse if present,
    # else encode on CPU with the cached VACE text encoder in a subprocess-free fallback.
    emb_path = WORK / "embeds.pt"
    if not emb_path.exists():
        sys.exit("embeds.pt missing — run the encode phase first (see stage_b pattern)")
    emb = torch.load(emb_path)
    pos = emb["pos"].to("mps", torch.bfloat16)

    src = Image.open(WORK / "frame.png").convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)

    t0 = time.time()

    def on_step(p, i, t, kw):
        print(f"[step {i+1}/{NUM_STEPS}] {time.time()-t0:.0f}s "
              f"mps_driver={torch.mps.driver_allocated_memory()/1e9:.1f}GB "
              f"sys_avail={psutil.virtual_memory().available/1e9:.1f}GB", flush=True)
        return kw

    out = pipe(
        image=src,
        prompt_embeds=pos,
        height=HEIGHT, width=WIDTH, num_frames=NUM_FRAMES,
        num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE,
        generator=torch.Generator("cpu").manual_seed(SEED),
        callback_on_step_end=on_step,
    ).frames[0]

    from diffusers.utils import export_to_video
    gen_dir = WORK / "gen"
    gen_dir.mkdir(exist_ok=True)
    for i, fr in enumerate(out):
        Image.fromarray((fr * 255).astype("uint8") if hasattr(fr, "astype") else fr).save(
            gen_dir / f"{i:04d}.png")
    export_to_video(out, str(WORK / "gen_preview.mp4"), fps=FPS_OUT)
    print(f"[turbo] DONE {time.time()-t0:.0f}s, final "
          f"mps_driver={torch.mps.driver_allocated_memory()/1e9:.1f}GB", flush=True)


if __name__ == "__main__":
    main()

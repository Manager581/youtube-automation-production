#!/usr/bin/env python3
"""
Test Wan 2.1 T2V-1.3B video generation locally on Apple Silicon.
Uses encode-then-delete strategy to keep memory under 12GB peak.

Model: Wan-AI/Wan2.1-T2V-1.3B-Diffusers (~29GB download, one-time)
Components:
  - Text encoder (UMT5-XXL): ~9.5GB in bfloat16 (loaded on CPU, deleted after encoding)
  - Transformer (1.3B): ~2.8GB in bfloat16 (MPS)
  - VAE: ~508MB in float32 (MPS)

Usage:
    tools/ltx-video/ltx_env/bin/python scripts/test_wan_video.py
"""

import gc
import os
import sys
import time
import psutil

MODEL_ID = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
MAX_MEMORY_GB = 15  # abort if we exceed this
OUTPUT_PATH = "output/wan_hotel_test.mp4"


def get_memory_gb():
    """Return current process RSS in GB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024**3)


def check_memory(stage: str):
    """Print memory usage and abort if too high."""
    mem = get_memory_gb()
    print(f"  [{stage}] Memory: {mem:.1f} GB")
    if mem > MAX_MEMORY_GB:
        print(f"  ABORT: Memory {mem:.1f}GB exceeds {MAX_MEMORY_GB}GB limit!")
        sys.exit(1)
    return mem


def main():
    print("=" * 60)
    print("WAN 2.1 T2V-1.3B — Local Video Generation Test")
    print("=" * 60)

    check_memory("startup")

    import torch
    check_memory("torch imported")

    # Check MPS availability
    if not torch.backends.mps.is_available():
        print("ERROR: MPS (Metal) not available on this system")
        sys.exit(1)

    print(f"\nDevice: MPS (Apple Silicon)")
    print(f"PyTorch: {torch.__version__}")

    from diffusers import AutoencoderKLWan, WanPipeline
    from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
    from diffusers.utils import export_to_video
    check_memory("diffusers imported")

    prompt = (
        "A dark hotel room at 3am, 1950s decor. A shadowy figure silhouetted against "
        "a dimly lit window. The window glass shatters outward and the figure falls through "
        "into the night. Noir cinematic lighting, dramatic, moody, atmospheric."
    )
    negative_prompt = (
        "Bright tones, overexposed, static, blurred details, subtitles, "
        "worst quality, low quality, ugly, deformed"
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)

    # ── Step 1: Load text encoder on CPU, encode prompt, then delete ──
    print("\n[1/4] Loading text encoder on CPU (this downloads ~22GB first time)...")
    print("       This may take a while on first run...")

    from transformers import AutoTokenizer, UMT5EncoderModel
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, subfolder="tokenizer")
    text_encoder = UMT5EncoderModel.from_pretrained(
        MODEL_ID, subfolder="text_encoder", torch_dtype=torch.bfloat16
    )
    check_memory("text encoder loaded")

    print("  Encoding prompt...")
    text_inputs = tokenizer(
        [prompt], padding="max_length", max_length=226,
        truncation=True, return_tensors="pt"
    )
    neg_inputs = tokenizer(
        [negative_prompt], padding="max_length", max_length=226,
        truncation=True, return_tensors="pt"
    )

    with torch.no_grad():
        prompt_embeds = text_encoder(
            text_inputs.input_ids, text_inputs.attention_mask
        ).last_hidden_state.to(torch.bfloat16)
        negative_prompt_embeds = text_encoder(
            neg_inputs.input_ids, neg_inputs.attention_mask
        ).last_hidden_state.to(torch.bfloat16)

    check_memory("prompts encoded")

    # Delete text encoder to free ~9.5GB
    del text_encoder, tokenizer, text_inputs, neg_inputs
    gc.collect()
    check_memory("text encoder deleted")

    # ── Step 2: Load VAE ──
    print("\n[2/4] Loading VAE...")
    vae = AutoencoderKLWan.from_pretrained(
        MODEL_ID, subfolder="vae", torch_dtype=torch.float32
    )
    check_memory("VAE loaded")

    # ── Step 3: Load pipeline (transformer only, text encoder already gone) ──
    print("\n[3/4] Loading transformer (1.3B)...")
    pipe = WanPipeline.from_pretrained(
        MODEL_ID, vae=vae, torch_dtype=torch.bfloat16,
        text_encoder=None, tokenizer=None,
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(
        pipe.scheduler.config, flow_shift=3.0  # 3.0 for lower res
    )
    pipe = pipe.to("mps")
    check_memory("pipeline on MPS")

    # ── Step 4: Generate ──
    print(f"\n[4/4] Generating video...")
    print(f"  Resolution: 320x512, Frames: 33 (~2s at 16fps)")
    print(f"  Steps: 25, Guidance: 5.0")
    print(f"  Prompt: {prompt[:60]}...")

    start_time = time.time()
    output = pipe(
        prompt_embeds=prompt_embeds.to("mps"),
        negative_prompt_embeds=negative_prompt_embeds.to("mps"),
        height=320,
        width=512,
        num_frames=33,
        num_inference_steps=25,
        guidance_scale=5.0,
        generator=torch.Generator("mps").manual_seed(42),
    )
    elapsed = time.time() - start_time

    check_memory("generation complete")

    frames = output.frames[0]
    export_to_video(frames, OUTPUT_PATH, fps=16)

    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"\nDONE: {OUTPUT_PATH} ({size_mb:.1f} MB, ~2s)")
    print(f"Time: {elapsed:.0f}s")
    print(f"Peak memory: {get_memory_gb():.1f} GB")
    print("=" * 60)


if __name__ == "__main__":
    main()

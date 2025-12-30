#!/usr/bin/env python3
"""Quick test script for Qwen2-VL local inference"""

from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

print("🧪 Testing Qwen2-VL with a single image...")

# Load model
print("📦 Loading model...")
model_path = "mlx-community/Qwen2-VL-2B-Instruct-4bit"
model, processor = load(model_path)
config = load_config(model_path)
print("✅ Model loaded!")

# Test with first available keyframe
import glob
keyframes = glob.glob("analysis/watop/*/keyframes/segment_0000.jpg")

if not keyframes:
    print("❌ No keyframes found. Run phase1c first to generate keyframes.")
    exit(1)

test_image = keyframes[0]
print(f"🖼️  Testing with: {test_image}")

# Simple prompt
prompt = "Describe what you see in this image in one sentence."

# Format prompt
formatted_prompt = apply_chat_template(processor, config, prompt, num_images=1)

# Generate
print("🔮 Generating description...")
result = generate(model, processor, formatted_prompt, [test_image], verbose=False)

print(f"\n✅ SUCCESS!\n")
print(f"Result: {result}")

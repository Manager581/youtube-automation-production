# Local MLX Vision Setup (M5 MacBook Pro - FREE & Unlimited)

## Why Local MLX?

✅ **100% FREE** - No API costs ever
✅ **UNLIMITED** - No rate limits or quotas
✅ **FAST** - Optimized for Apple Silicon (M5 chip)
✅ **PRIVATE** - Data never leaves your machine
✅ **RELIABLE** - No decommissioned models or quota changes

## Requirements

- **M5 MacBook Pro** (or any Apple Silicon Mac)
- **~22GB disk space** (for model download, one-time)
- **~16GB RAM** (during inference)
- **130GB total storage available** (you have this ✓)

## Installation (2 minutes)

```bash
# Make sure you're in your virtual environment
source venv/bin/activate

# Install MLX Vision and Pillow
pip install mlx-vlm pillow
```

That's it! The model will auto-download on first use.

## First Run (One-time 22GB Download)

When you first run Phase 1C, it will download the Llama 3.2 Vision 11B model:

```bash
python src/phase1c_visual_analyzer.py watop 10
```

**What happens:**
1. Downloads ~22GB model (takes 10-20 minutes depending on internet)
2. Caches model to `~/.cache/huggingface/`
3. **Every future run uses the cached model** (instant startup)

## Model Details

**Model:** Llama 3.2 Vision 11B (4-bit quantized)
- **Size:** ~22GB (4-bit quantization reduces from 44GB)
- **Quality:** Same as the 11B model you tried with Groq (before it was decommissioned)
- **Speed:** ~2-3 seconds per image on M5 chip
- **Memory:** ~16GB RAM during use

## Usage

Once installed, just run normally:

```bash
# Analyze top 10 videos
python src/phase1c_visual_analyzer.py watop 10

# Analyze bottom 10 videos
python src/phase1c_visual_analyzer.py watop 10 --bottom
```

**No API keys needed. No quotas. Runs forever for free.**

## Performance Estimate

- **Per video:** ~28 classifications × 2.5 sec each = ~70 seconds
- **10 videos:** ~12 minutes total
- **Cost:** $0.00

Compare to APIs:
- OpenAI: $0.12 but limited by payment
- Gemini: Free but 20 req/day limit (useless)
- Groq: Models decommissioned (broken)

## Troubleshooting

**"mlx-vlm not installed" error:**
```bash
pip install mlx-vlm pillow
```

**First run stuck downloading:**
- Model is large (22GB), download takes time
- Check internet connection
- Progress will show in terminal

**"Out of memory" error:**
- Close other apps to free RAM
- 4-bit model should fit in 16GB
- If still fails, restart Mac

**Model already downloaded but re-downloading:**
- Check `~/.cache/huggingface/hub/` for existing model
- MLX should auto-detect cached models

## Benefits for 95% Automation

With local MLX, you can:
- Classify **unlimited** videos at no cost
- Scale to analyze 100s of creators
- No API quota concerns
- Build production automation without recurring costs

This is the foundation for true 95% automation! 🎯

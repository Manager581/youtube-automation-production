# Groq API Setup (Free Tier - 1,000 req/day)

## Get Your Free API Key

1. **Visit Groq Console:**
   - Go to: https://console.groq.com/keys
   - Sign up or log in with your account

2. **Create API Key:**
   - Click "Create API Key"
   - Give it a name (e.g., "youtube-automation")
   - Copy the generated API key

## Install Required Library

```bash
pip install groq
```

## Set Environment Variable

### For Current Session (Mac/Linux):
```bash
export GROQ_API_KEY='your-api-key-here'
```

### Make it Permanent (Mac/Linux):
Add to your `~/.zshrc` or `~/.bash_profile`:
```bash
echo "export GROQ_API_KEY='your-api-key-here'" >> ~/.zshrc
source ~/.zshrc
```

## Free Tier Limits

- **1,000 requests per day** (50x more than Gemini!)
- **30 requests per minute** rate limit
- **No credit card required**
- Model: `llama-3.2-90b-vision-preview` (90B parameter vision model)

## Test Visual Classification

Once you have your API key set up, run Phase 1C visual analysis:

```bash
# Analyze top 10 videos
python src/phase1c_visual_analyzer.py watop 10

# Analyze bottom 10 videos
python src/phase1c_visual_analyzer.py watop 10 --bottom
```

This will:
1. Detect scenes in videos
2. Extract keyframes at scene boundaries
3. Map visuals to script words
4. **Classify visual content using Groq Llama Vision** (content type, subject, source indicators)

Results saved to:
- `analysis/watop/visual_analysis_top.json` (top performers)
- `analysis/watop/visual_analysis_bottom.json` (bottom performers)

## Troubleshooting

**"GROQ_API_KEY not set" error:**
- Verify you've exported the key: `echo $GROQ_API_KEY`
- Make sure you've sourced your shell config: `source ~/.zshrc`

**"groq not installed" error:**
- Run: `pip install groq`
- Make sure you're in your virtual environment

**Rate limit errors:**
- Free tier allows 30 requests/min, 1,000/day
- If you hit limits, wait a minute and continue

## Model Details

**llama-3.2-90b-vision-preview:**
- 90 billion parameter model with vision capabilities
- Supports image reasoning, visual Q&A, caption generation
- Better quality than smaller vision models
- Fast inference thanks to Groq's hardware acceleration

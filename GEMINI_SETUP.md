# Google Gemini API Setup (Free Tier)

## Get Your Free API Key

1. **Visit Google AI Studio:**
   - Go to: https://aistudio.google.com/app/apikey
   - Sign in with your Google account (any Google account works)

2. **Create API Key:**
   - Click "Create API Key"
   - Select "Create API key in new project" (or use existing project)
   - Copy the generated API key

## Install Required Libraries

```bash
pip install google-genai Pillow
```

## Set Environment Variable

### For Current Session (Mac/Linux):
```bash
export GOOGLE_API_KEY='your-api-key-here'
```

### Make it Permanent (Mac/Linux):
Add to your `~/.zshrc` or `~/.bash_profile`:
```bash
echo "export GOOGLE_API_KEY='your-api-key-here'" >> ~/.zshrc
source ~/.zshrc
```

## Free Tier Limits

- **1,500 requests per day** (more than enough for analysis)
- **15 requests per minute** rate limit
- **No credit card required**
- Model: `gemini-1.5-flash` (fast, free, multimodal)

## Test Visual Classification

Once you have your API key set up, run Phase 1C visual analysis:

```bash
python src/phase1c_visual_analyzer.py watop 10
```

This will:
1. Detect scenes in top 10 WATOP videos
2. Extract keyframes at scene boundaries
3. Map visuals to script words
4. **Classify visual content using Gemini** (content type, subject, source indicators)

The visual classifications will be saved to `analysis/watop/visual_analysis.json`

## Troubleshooting

**"GOOGLE_API_KEY not set" error:**
- Verify you've exported the key: `echo $GOOGLE_API_KEY`
- Make sure you've sourced your shell config: `source ~/.zshrc`

**"google-genai not installed" error:**
- Run: `pip install google-genai Pillow`
- Make sure you're in your virtual environment
- If you have the old `google-generativeai` package, uninstall it first:
  ```bash
  pip uninstall google-generativeai
  pip install google-genai
  ```

**Rate limit errors:**
- Free tier allows 15 requests/min, 1,500/day
- Script automatically samples max 20 keyframes per video to stay under limits
- If you hit limits, wait a minute and continue

#!/bin/bash
# Whisper-align each chapter WAV and check for hallucinations
# Run AFTER generate_chapters.sh completes

set -e
cd /Users/jefflawrence/Documents/youtube-automation-production
export PATH="/opt/homebrew/bin:/Users/jefflawrence/.local/bin:$PATH"

PYTHON=venv/bin/python
ALIGNER="pipeline_v2.narration_aligner"
OUT_DIR=audio/breaking_law/chapters

# SSL fix for Whisper/tiktoken on Python 3.13
export SSL_CERT_FILE=$($PYTHON -c "import certifi; print(certifi.where())")

CHAPTERS=(
  "ch0_cold_open"
  "ch1_the_formula"
  "ch2_the_data"
  "ch3_the_machines"
  "ch4_the_rent"
  "ch5_the_reckoning"
)

# ch3 was generated as two halves (ch3a + ch3b) and concatenated via ffmpeg

FAILED=0

for ch in "${CHAPTERS[@]}"; do
  WAV="${OUT_DIR}/voice_${ch}.wav"
  SCRIPT="scripts/chapters/${ch}.txt"
  ALIGN="${OUT_DIR}/align_${ch}.json"

  if [ ! -f "$WAV" ]; then
    echo "ERROR: Missing WAV: $WAV"
    FAILED=$((FAILED + 1))
    continue
  fi

  echo ""
  echo "============================================"
  echo "  Aligning: $ch"
  echo "============================================"

  $PYTHON -m $ALIGNER \
    --narration "$WAV" \
    --script "$SCRIPT" \
    --output "$ALIGN" \
    --model base

  echo "=== Alignment done for $ch ==="

  # Hallucination check: compare Whisper transcript vs script
  echo ""
  echo "  Checking for hallucinations..."
  $PYTHON -c "
import json, re

with open('$ALIGN') as f:
    align = json.load(f)

with open('$SCRIPT') as f:
    script = f.read()

# Strip markers from script
clean_script = re.sub(r'\[.*?\]', '', script).lower()
script_words = set(clean_script.split())

# Get Whisper words
whisper_text = ' '.join(s['text'] for s in align.get('sentences', []))
whisper_words = set(whisper_text.lower().split())

# Check overlap
if len(script_words) == 0:
    print('  WARNING: Empty script')
elif len(whisper_words) == 0:
    print('  WARNING: Empty Whisper output')
else:
    overlap = len(script_words & whisper_words)
    total = len(script_words)
    pct = (overlap / total) * 100
    print(f'  Word overlap: {overlap}/{total} ({pct:.0f}%)')
    if pct < 50:
        print(f'  *** HALLUCINATION DETECTED — overlap {pct:.0f}% < 50% threshold ***')
        print(f'  *** REGENERATE THIS CHAPTER ***')
    elif pct < 70:
        print(f'  WARNING: Low overlap ({pct:.0f}%). May have minor issues.')
    else:
        print(f'  PASS: Good alignment ({pct:.0f}%)')

# Check for repeated phrases (hallucination signature)
words = whisper_text.lower().split()
from collections import Counter
trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
tc = Counter(trigrams)
repeated = [(t, c) for t, c in tc.most_common(5) if c > 3]
if repeated:
    print(f'  WARNING: Repeated phrases (possible hallucination):')
    for t, c in repeated:
        print(f'    \"{t}\" x{c}')
else:
    print(f'  No repeated phrases detected.')
"

done

echo ""
echo "============================================"
if [ $FAILED -gt 0 ]; then
  echo "  $FAILED chapters FAILED alignment"
  exit 1
else
  echo "  All chapters aligned and checked!"
  ls -lh "$OUT_DIR"/align_ch*.json
fi

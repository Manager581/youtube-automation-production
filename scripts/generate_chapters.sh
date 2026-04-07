#!/bin/bash
# Generate voice per-chapter to avoid F5-TTS OOM on M5 24GB
# Each chapter runs in its own process — model unloads between runs

set -e
cd /Users/jefflawrence/Documents/youtube-automation-production
export PATH="/opt/homebrew/bin:/Users/jefflawrence/.local/bin:$PATH"
# SSL fix for Whisper/tiktoken on Python 3.13
export SSL_CERT_FILE=$(venv/bin/python -c "import certifi; print(certifi.where())")

PYTHON=venv/bin/python
VOICE_GEN=pipeline/voice_generator.py
REF_NEUTRAL=assets/voice/voice_neutral.wav
REF_TENSE=assets/voice/voice_tense.wav
REF_ENERGIZED=assets/voice/voice_energized.wav
OUT_DIR=audio/breaking_law/chapters

mkdir -p "$OUT_DIR"

CHAPTERS=(
  "ch0_cold_open"
  "ch1_the_formula"
  "ch2_the_data"
  "ch3a_the_machines"
  "ch3b_the_machines"
  "ch4_the_rent"
  "ch5_the_reckoning"
)

for ch in "${CHAPTERS[@]}"; do
  SCRIPT="scripts/chapters/${ch}.txt"
  OUT="${OUT_DIR}/voice_${ch}.wav"

  if [ -f "$OUT" ] && [ $(stat -f%z "$OUT") -gt 10000 ]; then
    echo "=== SKIP $ch (already exists: $OUT) ==="
    continue
  fi

  echo ""
  echo "============================================"
  echo "  Generating: $ch"
  echo "============================================"

  $PYTHON $VOICE_GEN \
    --ref-neutral "$REF_NEUTRAL" \
    --ref-tense "$REF_TENSE" \
    --ref-energized "$REF_ENERGIZED" \
    --auto-transcribe \
    --script "$SCRIPT" \
    --out "$OUT"

  echo "=== DONE $ch ==="
  echo ""

  # Force Python/MPS cleanup between chapters
  sleep 2
done

echo ""
echo "All chapters generated. Files:"
ls -lh "$OUT_DIR"/voice_ch*.wav

#!/bin/bash
# exclude_venvs_from_icloud.sh
# Excludes the Python venvs from iCloud sync (and thus from eviction) by renaming
# them to a `.nosync` suffix (which iCloud Drive ignores) and leaving a symlink so
# `venv/bin/python` etc. keep working. Safe: refuses to run if any file is still
# dataless (st_blocks==0), so nothing gets stranded.
#
# Reversible: rm the symlink, mv the .nosync dir back.
# New-Mac restore: the venv won't be there (correct — venvs aren't portable);
# rebuild with `python3 -m venv venv && venv/bin/pip install -r requirements.txt`.
set -u
cd /Users/jefflawrence/Documents/youtube-automation-production || exit 1

count_dataless() {  # $1 = dir
  find "$1" -type f 2>/dev/null | while read -r f; do
    [ "$(stat -f %b "$f")" = "0" ] && echo x
  done | wc -l | tr -d ' '
}

for v in "venv" "tools/ltx-video/ltx_env"; do
  if [ -L "$v" ]; then echo "SKIP $v — already a symlink (excluded)"; continue; fi
  if [ ! -d "$v" ]; then echo "SKIP $v — not found"; continue; fi
  n=$(count_dataless "$v")
  if [ "$n" -ne 0 ]; then
    echo "ABORT $v — still $n dataless files; must be fully local before excluding"; exit 1
  fi
  base=$(basename "$v")
  mv "$v" "${v}.nosync" || { echo "FAILED to rename $v"; exit 1; }
  ( cd "$(dirname "$v")" && ln -s "${base}.nosync" "$base" )
  echo "EXCLUDED $v -> ${v}.nosync (+ symlink)"
done

echo "--- verify imports work through the symlinks ---"
venv/bin/python -c "import torch; print('  main venv: torch', torch.__version__, 'OK')" || echo "  MAIN VENV IMPORT FAILED"
tools/ltx-video/ltx_env/bin/python -c "import torch; print('  ltx_env: torch', torch.__version__, 'OK')" || echo "  LTX_ENV IMPORT FAILED"
echo "EXCLUDE_DONE"

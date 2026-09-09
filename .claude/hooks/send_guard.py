#!/usr/bin/env python3
"""PreToolUse guard: a video may leave this machine ONLY as deliveries/<lane>/<stem>_<sha8>.mp4 with its DELIVERY_CHECKLIST beside it.
Blocks SendUserFile on any other .mp4/.mov/.webm, and Bash commands that `open`/copy a render out of output/ to Desktop/Downloads/iCloud."""
import json, os, re, sys
try: inp = json.load(sys.stdin)
except Exception: sys.exit(0)
tool = inp.get("tool_name", ""); ti = inp.get("tool_input", {}) or {}; repo = os.getcwd()
def blocked(msg): print(msg, file=sys.stderr); sys.exit(2)
if tool == "SendUserFile":
    for f in ti.get("files", []) or []:
        if re.search(r"\.(mp4|mov|webm|mkv)$", f, re.I):
            p = os.path.abspath(f); rel = os.path.relpath(p, repo)
            if not rel.startswith("deliveries" + os.sep): blocked(f"send_guard: {rel} is not a deliverable. Only deliveries/<lane>/<stem>_<sha8>.mp4 produced by scripts/deliver.py may be sent (CLAUDE.md rule 8).")
            stem = os.path.splitext(os.path.basename(p))[0]; ck = os.path.join(os.path.dirname(p), f"DELIVERY_CHECKLIST_{stem}.json")
            if not os.path.exists(ck): blocked(f"send_guard: no DELIVERY_CHECKLIST for {rel}; run scripts/deliver.py first.")
            if json.load(open(ck)).get("delivered_as") and os.path.abspath(json.load(open(ck))["delivered_as"]) != p: blocked("send_guard: checklist does not name this file.")
elif tool == "Bash":
    cmd = ti.get("command", "")
    if re.search(r"\bopen\b[^|;&]*\.(mp4|mov|webm)\b", cmd) and "deliveries/" not in cmd: blocked("send_guard: opening a render outside deliveries/ is the owner's eyes on an ungated cut. Run scripts/deliver.py first.")
    if re.search(r"\b(cp|mv|rsync|ditto)\b[^|;&]*output/[^|;&]*\.(mp4|mov|webm)\b[^|;&]*(Desktop|Downloads|iCloud|Mobile Documents|Dropbox|Drive)", cmd): blocked("send_guard: copying a render out of output/ bypasses deliver.py.")
sys.exit(0)

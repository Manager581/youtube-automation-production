# Schedules — recurring pipeline reads (PIPELINE_OVERHAUL_PLAN build step 3)

## own-channel-read (weekly, Mondays 09:00 local)

Runs `scripts/own_channel_read.py`: reads public metrics for every upload on the
owned channels, records views in `publish_ledger.json`, writes a dated read JSON +
summary under `reads/`, and appends to `reads/READS_LEDGER.md`.

**Install (one-time, owner runs it):**

```bash
cp schedules/com.youtube-automation.own-channel-read.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.youtube-automation.own-channel-read.plist
```

Uninstall: `launchctl unload ~/Library/LaunchAgents/com.youtube-automation.own-channel-read.plist` and delete the file.
Depends on `yt-dlp` on PATH (miniforge bin is included in the plist's PATH).
Note: launchd skips a run if the Mac is asleep at the trigger time; the next
manual `python3 scripts/own_channel_read.py` catches up — reads are idempotent
per date.

Day-14 / day-90 strategy reads (plan §S11) stay owner decisions off the weekly
summaries; commit `reads/` output when a read lands.

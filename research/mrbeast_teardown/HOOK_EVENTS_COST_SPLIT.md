# Hook events: generation vs edit-layer (from hook_event_ledger_v1_0-45s.json, 2026-08-31)

187 events in 45 s → ~17 unique source shots (6 are archive stills = image gens) + ~120 post operations.
≈ 1 generation per 11 events. Two-thirds of felt density is edit-layer and costs $0 once templates exist.

| class | n | cost |
|---|---|---|
| graphic_overlay 21 + text_on 5 + text_off 10 + text_animate 11 + color_shift 14 | 61 | $0 post |
| zoom_in 10 + zoom_out 8 + speed_ramp 1 (all DIGITAL per ledger) | 19 | $0 post |
| camera_move 18 (15 drift/digital push; ~3 real moves: whip-tilt 32.25, crate orbit 38.9) | 18 | ~3 gens |
| hard_cut 24 → 17 distinct setups (7 cuts return to an existing angle) | 24 | 17 gens |
| subject_change 38 + motion_spike 21 + angle_change 6 (action INSIDE generated clips) | 65 | $0 extra; #1 reject risk |

Budget law: generation scales with UNIQUE SETUPS (~1/3 s in hooks, ~1/6-7 s elsewhere), NOT event density.
Reference proof: 0-12 s = 1 real cut, 13 visual transitions, one take + digital zooms + graphics.
Where: FFmpeg engine does all ~120 unattended (zoompan, xfade/whiteout, hstack, setpts, eq/curves, gblur bloom,
drawtext/ASS timed text, ducking). DaVinci = manual polish only (Fusion 3D animated titles, dissolves — no keyframe API).
Possible Studio semi-auto: body glow-halo via scriptable CreateMagicMask (untested; one-clip prototype).
Multicam disadvantage vs reference: we pay per angle → derive mediums by digital crop from wider/1080p masters; AMBER/VACE composites for inserts.

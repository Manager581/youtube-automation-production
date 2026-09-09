# Resolve 20.3.2 Studio — Scripting Capability Table (verified 2026-08-31)

Ground truth: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/README.txt`
(1,012 lines, "Last Updated: 7 Oct 2025") read in full + samuelgursky/davinci-resolve-mcp v2.108.0 measured
ledger (live-tested on Studio 20.3.2.9). Installed build: 20.3.20009 (Studio, paid). Resolve 21 = FREE update.

**Architectural fact:** an MCP is a wrapper over Blackmagic's scripting API — it can NEVER add a capability
the API lacks. The 353-tool MCP has 100% API coverage and still routes every gap below through FFmpeg
pre-baking. Building our own MCP adds nothing (and violates the no-parallel-solutions rule).

| Capability | Verdict | Detail |
|---|---|---|
| **Video clip at exact timestamp** | ✅ CAN (traps) | `AppendToTimeline([{mediaPoolItem, startFrame, endFrame, mediaType, trackIndex, recordFrame}])` — documented in OUR 20.3.2 README line 221; positioned appends live-validated on 20.3.2.9. TRAPS: recordFrame is TIMELINE-ABSOLUTE (add the 01:00:00:00 offset = 86400@24 or clip renders as ~0-frame stub); overlap with existing item = SILENT drop (earlier item wins); errored chunks discarded by save; phantom null-id returns → always re-read + count-verify after append. CLAUDE.md's "ignores recordFrame" scar predates BMD's 20.0.1/20.2.2 fixes — one cheap prototype before relying on it. |
| **Audio (VO/SFX/music) at exact timestamp** | ✅ CAN (traps) | Same clipInfo with `mediaType:2` + `trackIndex` (20.2.2 fixed large audio trackIndex). `Timeline.AddTrack("audio",{...})` for targeted tracks. TRAP: WAV fps is frozen at PROJECT frame rate on import — always read the clip's FPS property (a wrong assumption landed a clip 7min52s off). |
| **Audio volume/gain/fade per clip or track** | ❌ IMPOSSIBLE via any API, any version | Zero grep hits for gain/fade; `SetProperty(Volume/Level/Gain)` returns False (measured 19.1.3.7, 20.3.2.9, 21.0.0). Only wholesale `ApplyFairlightPresetToCurrentTimeline` (never yet observed returning True). → PREMIX in FFmpeg (our standing rule, independently re-derived by the MCP project's own mix_plan tools). |
| **Still image at timestamp w/ duration** | ⚠️ TRAP | clipInfo documents endFrame with no stills exception, but stills historically ignore endFrame (land at Preferences default still duration). Route: snapshot `Project.GetSetting()` to find the still-duration key, set it before appending. Prototype required. |
| **Static zoom/pan/crop/opacity on a clip** | ✅ CAN today | `TimelineItem.SetProperty`: Pan, Tilt, ZoomX/Y, ZoomGang, RotationAngle, AnchorPointX/Y, Pitch/Yaw, Flip, Crop*, CropSoftness, CompositeMode (34 modes), Opacity, Distortion, RetimeProcess, MotionEstimation, Scaling, ResizeFilter. ALL STATIC single values. `Speed` is NOT settable (returns False). |
| **ANIMATED zoom/pan (Ken Burns), keyframes** | ❌ IMPOSSIBLE via API | ZERO keyframe-WRITE methods at any version (only read-side GetKeyframeAtIndex + a UI-mode enum). `DynamicZoomEase` exists but no key enables Dynamic Zoom or sets its rects. Escape hatches: (a) FFmpeg pre-bake — the MCP ledger's own standing order: "bake stills motion with ffmpeg when unattended output is required"; (b) Fusion comp scripting — CAN animate but measured SILENT RENDER FAILURES (input set between Comp.Lock/Unlock reads back correctly but doesn't render; unwired MediaOut silently bypasses) → treat as human-in-loop; (c) FCPXML import carries some structure. |
| **Titles / Text+ at chosen track+frame** | ⚠️ WORKAROUND | Six `Insert*IntoTimeline` methods take NO position/track args (land at Source Track Selector target). Measured fix: NESTED-TIMELINE route — build title on its own timeline, place that timeline as a clip via AppendToTimeline → "lands on the requested track at the requested frame, exactly." Editing title text after placement needs 21.0.4+. |
| **Transitions (dissolve/crossfade)** | ❌ IMPOSSIBLE via live API | No Add/Create-transition method exists (dir() on 21.0.4.5). Workarounds: author in FCP7 XML and `ImportTimelineFromFile` (measured: BUILT a 59-frame dissolve, 572/573 clips exact) — or bake crossfades in FFmpeg (our engine). NOTE: the MCP's one-call `drt.assemble_from_interchange` FLATTENS transitions to cuts; direct ImportTimelineFromFile carries more (OTIO LinearTimeWarp/EDL M2 = constant retimes incl. reverse). |
| **Markers, render jobs, presets, in/out ranges** | ✅ CAN today | AddMarker (frame/color/note/duration/customData) everywhere; SetRenderSettings (MarkIn/MarkOut/size/fps/quality/alpha), AddRenderJob, StartRendering, GetRenderJobStatus, render presets, RenderWithQuickExport. |
| **Fusion engine scripting (motion graphics)** | ⚠️ EXISTS, undocumented | `fusionscript.so` + `fuscript` verified on disk; `resolve.Fusion()` opens the full Fusion API (comp.AddTool, Text+, keyframed tools) — but ships with NO documentation (introspect) and has the silent-render-failure ledger entries above. Prototype with rendered-frame proof (PSNR vs baseline), never trust GetInput readback. |
| **Studio AI, scriptable TODAY on 20.3.2** | ✅ | TranscribeAudio, CreateSubtitlesFromAudio, DetectSceneCuts, CreateMagicMask, **SmartReframe** (16:9→9:16 — kills the Opus Clip case), Stabilize, VoiceIsolation, Fairlight presets. 21.x-only (+ UI-downloaded AI Extras): AnalyzeForIntellisearch (BUILD-only, NO query API), GenerateSpeech, speaker detection. IntelliScript: ZERO API surface. Guard every AI/render call with `if result is True:` (truthy error-STRING trap). |

**Net for the pipeline:** Resolve scripting is a viable clip-placer/renderer today, but the three things that
make an edit feel alive — animated moves, transitions, the audio mix — are exactly what NO API (and therefore
no MCP, ours or anyone's) can do. FFmpeg pre-baking stays the engine; Resolve = polish + SmartReframe layer.
Our architecture is what the API forces on everyone, including the 2.3K-star MCP project itself.

---

## 2026-09-09 UPDATE — Blackmagic shipped a NATIVE MCP server in Resolve 21.1

**Verified:** Resolve 21.1 released 2026-09-08 (IBC 2026), free update, ~100+ new tools, and it includes a
**first-party MCP server** for Claude / ChatGPT-Codex. Corroborated by CG Channel, Sports Video Group,
digitalproduction, Newsshooter, ProVideo Coalition. Blackmagic's own marketing "what's new" page does NOT
mention MCP (checked 2026-09-09) — it's in the release/press coverage, not the feature grid.
Installed here = **20.3.2 Studio** → 21.1 is a free upgrade.

**What this changes:** removes the install/bridge friction of samuelgursky's community MCP. Nothing else.
An MCP is still a wrapper over the same scripting API, so the table above still governs what is possible.

**UNVERIFIED CLAIM worth one cheap measurement:** one second-hand blog (explainx.ai) lists "transitions"
among the native MCP's operations. The table above says NO Add/Create-transition method exists at 21.0.4.5.
If Blackmagic added transition methods in 21.1 that is a real architectural change — measure it with
`dir()` on a 21.1 TimelineItem/Timeline before believing any blog. Do NOT re-plan around it until measured.

**Trigger video (Danny Why, "ChatGPT Just Changed YouTube Forever", 2026-09-09, 13:59):** demo = Codex +
Resolve MCP → `TranscribeAudio` → cut pauses/retakes from the transcript → place clips on a new timeline.
That is exactly the ✅ CAN rows above; our whisperx + FFmpeg path already does it unattended at $0.
Two things the video does NOT show: (a) any animated move, transition, or audio-level automation done by
Resolve — the "motion graphics" are pre-rendered Higgsfield clips PLACED on a track (placement, not
animation), so the three ❌ IMPOSSIBLE rows are untouched; (b) pure MCP control — at 09:07 the creator
says "it started moving my mouse", i.e. part of the run was computer-use driving the Resolve UI, which is
not reproducible headlessly. Higgsfield is metered credits + an affiliate link → fails the no-API-spend rule.

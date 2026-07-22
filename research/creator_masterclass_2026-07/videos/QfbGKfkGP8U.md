# Jonas Rankl — "How to Edit VIRAL Text Commentary Shorts (Full Tutorial)" (QfbGKfkGP8U, 16:49, 66K views)

## What the video is
A CapCut screen-recorded tutorial that clones one viral "text commentary" Short beat-for-beat: a reused TikTok clip (kid crying at dinner) with tracked on-screen captions replacing voiceover. Wrapper claims: a channel in this style did 600M views in 30 days (~$30-40K), and Jonas has made "$500K profit in a year" running reused-content Shorts channels.

## What's actually shown (evidence)
- [~01:01] The only "proof": toggling YouTube Studio revenue currency USD→EUR (~$500K → ~€440K) and back. Shows a dashboard renders a number; proves nothing about source, content style, or that revenue survived monetization review. "Profit" vs revenue conflated.
- [01:32–15:52] A genuine, complete edit recreation in CapCut with real settings — this part is verifiable and mechanical (see tactics).
- No channel names, no upload workflow, no policy documentation. The 600M-view channel claim implies ~$0.05-0.07 Shorts RPM — consistent with known Shorts rates, which itself confirms Shorts are pennies-per-view next to bizdoc long-form ($10-25 RPM).

## Credibility
Low-to-medium. The editing tutorial is real and competent. The money framing is a funnel: Typeform "apply to work with me 1-on-1" (coaching), ElevenLabs + vidIQ affiliate links, and an Instagram DM lead magnet ("message me 'sound' for my SFX pack"). His core monetization claim — "text commentary transforms reused content, so it's monetizable" — is asserted, never evidenced, and is the most dangerous line in the video.

## Tactics extracted (mechanical)
1. **Recreate-the-winner workflow**: import the exact viral video into the timeline as reference; cut your raw footage into *his* order; clone every effect beat-for-beat. (= our viral_recreation_spec method, at Shorts scale. CONFIRM.)
2. **Vignette spotlight w/ tracking**: full-scale black layer → circle mask → invert → feather ≈21, opacity ≈70 → keyframe mask position to follow subject. A portable attention-guide. (NEW as an implemented overlay; maps to playbook editing.json attention guides.)
3. **Punch-in zooms**: keyframe scale+position a few frames apart on reaction beats (face, spoon). CONFIRM (edit grammar).
4. **Freeze/screenshot beat**: export still frame from timeline, re-import as its own beat. CONFIRM (we do stills natively).
5. **Caption color hierarchy**: line 1 bold+yellow (setup), body white, shock words red bold (Arial Bold); minimal black background block; typewriter animation on reveal captions ("but why"); track captions to head via motion-track (nose/eyebrow — flaky) or manual position keyframes. NEW packaging grammar for verticals.
6. **SFX palette economy**: the entire viral Short uses only 3 SFX — whooshes on cuts/zooms (speed-matched to motion, mixed quiet), one flash hit, one end "ding". CONFIRM+nuance of "sound on every cut": small reused palette, not variety.
7. **Letterbox format**: black bars top/bottom to shrink the frame — engagement-bait framing, trivially FFmpeg-able.

## Policy notes
The claim "adding text every second = transformative = monetizable" is unproven and risky. Under the July 15 2025 inauthentic-content policy, mass-produced reused clips with low-value overlays are exactly the target; text restating what's on screen is what reviewers flag. Separately, wholesale TikTok clip reuse is copyright exposure regardless of YPP status — he never mentions licensing. Nothing here changes our posture: we build original composited footage; do NOT adopt full-clip reuse.

## What we apply
- **Rexcaped**: add vignette-spotlight (feathered inverted circle, ~70% opacity, tracked) as an FFmpeg overlay in the edit engine's attention-guide kit; TEST one vertical Short cut from Video 1's best 30-45s using the caption hierarchy + 3-SFX palette (whoosh/hit/ding already in library).
- **Prehistoric POV**: TEST one text-commentary Short from existing POV clips — captions instead of VO ($0 marginal cost), tracked text on subject.
- **Bizdoc**: nothing now; caption color hierarchy only if we later do Shorts cutdowns.

## Verdict
The business model is IGNORE (reused content + coaching funnel, contradicts our fair-use rules). The edit mechanics are the real value: ADOPT the vignette-spotlight and caption hierarchy, TEST vertical Shorts repurposing, CONFIRM recreate-the-winner and SFX-on-cut, which we already systematized better than he does.

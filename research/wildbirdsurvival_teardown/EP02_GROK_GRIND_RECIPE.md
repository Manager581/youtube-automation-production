# EP02 — the Grok i2v grind: the working recipe

_Written 2026-07-23 after proving one clip end-to-end. Every step below was executed, not assumed._

## ⚡ SESSION-5 ADDENDUM (2026-07-23 night, 5/88 done — read this before the old text)

**The paste requirement is TAB VISIBILITY, nothing else.** The claude-in-chrome MCP tab is
usually a HIDDEN background tab, and Chrome will not deliver the OS clipboard to a hidden tab —
that is the entire mystery behind every "first paste no-ops" observation. The reliable loop:
1. `preview_crop.py` the shot's seed → always feed a **1264×720** PNG; `osascript` it to clipboard.
2. Navigate the MCP tab to grok.com/imagine, then set `document.title='MCPTAB-GRIND'` via JS.
3. AppleScript: find the tab by that title → `set active tab index` + `set index of w to 1`
   (AppleScript tab ids ≠ CDP tabIds — always match by the title marker).
4. **In ONE `browser_batch` call**: click the composer + `key cmd+v` (no gap for the Claude app
   to steal focus). Verify the attached blob `<img>` reports exactly 1264×720.
5. Prompt via execCommand, verify length; check 720p/6s pills (6s can flip to 10s); submit;
   fetch→blob→`<a download>` (grok.com downloads have not tripped the multi-download flag —
   keep it that way by staying on fresh /imagine loads between generations).
- Do NOT use System Events keystrokes or cliclick for this flow: the Claude desktop app
  re-fronts itself between tool calls, so OS-level input lands in the wrong app.

**WIDE shots: remove ALL blood attention.** S003 take 1 invented a bright red pool ON THE ROCK —
at WS scale the stain is a sub-visible speck, and the blood rider itself directs the model to
paint blood it can't see (the S079 mechanism, now proven on a live gen). Fix that shipped:
`has_blood=false`, zero red mentions, plus a hard count clause ("the number of birds never
changes — exactly N in every frame"; take 1 also multiplied the finches). Take 2 ACCEPTED.

**A2's wet mark + beak-in-contact + full-window shots = structurally unstable.** S005 needed
5.8 s of its 6.04 gen; three takes gave pull-back strings / oscillating red / a monotonic run.
Unlike S002 (ships 2.3 s from the stable early window, clip_in=0.6, ACCEPTED take 1 on the
repaired pin-prompt), there is no window escape when dur ≈ 6 s. Policy: best-of-N ships with a
note, and the fallback is an **AMBER/VACE masked-crop stabilization of the mark region**
(proven pipeline, ~22 min/beat, $0) — not more takes. S005 ships take 2 under this policy.

**The repaired pin-pattern works.** S002 (the shot that killed take 1 last session) was accepted
on its first take with the new prompt: bill locked all 9 frames, one blink, stain stable through
the shipped window. When a blood shot fails, fix the PROMPT to pin the feeding bird whole-body
and name-and-pin the existing streak/filaments — do not re-litigate the seed.

## ⭐ THE FIVE STEPS THAT ACTUALLY PRODUCE AN ACCEPTED CLIP

Proven on S004, which was **rejected on take 1 and accepted on take 2** — the difference was
step 1 alone.

1. **PRE-CROP THE SEED to the shot's framing, and feed the crop.** i2v begins on frame 1 and
   *never re-frames*, so a prompt asking for a tighter shot than its still simply returns the
   still's framing. S004 take 1 came back a full-body wide against a prompt demanding a tight
   medium. Take 2, from a `506,75,1058,595` crop, delivered exactly the prompt. The box lives in
   the shot's **`seed_crop`** field; render and LOOK at it first:
   ```bash
   venv/bin/python research/wildbirdsurvival_teardown/preview_crop.py SEED.png x,y,w,h /tmp/try.png
   ```
   Keep upscale ≤ ~2.5× (the tool prints it) or the source goes soft and reads as fake.
   **This is also how 73 of the 88 shots get DISTINCT vantages from 25 stills** — without it the
   21 shots on `hero_still_A_booby_finch.png` all render as the same wide shot, which is the
   glitchy-loop failure that got `rough_cut_v1` rejected.
2. **Use the shot's current prompt.** For blood shots it has already been respec'd to pin the
   feeding bird's bill absolutely still and give the motion to things that cannot touch the
   stain. **That fix is empirically confirmed:** S004's stain held perfectly stable across all
   9 strip frames, where S002's ran into a streak by 4.4 s on the same seed family.
3. **Generate** — 720p, 6 s, seed attached (verify the blob `<img>` reports the crop's exact
   pixel size), prompt inserted byte-exact.
4. **Frame-strip and LOOK at it.** Non-negotiable; both rejections this session looked fine in
   motion and only failed on the strip.
5. **Pick the shipped window with `clip_in`.** Grok always returns 6.04 s but most shots ship
   1.5–5 s, so *which* window matters more than the length. S004 ships 1.4 s and its whole beat
   — the defensive gape — is at ~1.0–2.4 s, so `clip_in: 1.0`. A blind trim from 0 would have
   shipped the static opening and dropped the beat entirely. The assembler honours `clip_in`.

Both `seed_crop` and `clip_in` go through `apply_defect_edits.py` like any other edit; they are
source-side fields and cannot break timeline tiling.

---

## The browser method that works (this replaces guesswork)

**Attaching the seed — `key` with the chord in `text`, NOT the `modifiers` param.**
This is the whole unlock and it cost several dead ends to find:

```
osascript -e 'set the clipboard to (read (POSIX file "/…/SEED.png") as «class PNGf»)'
computer{action:"left_click", coordinate:<composer>}
computer{action:"key", text:"cmd+v"}          # <-- chord IN text. Real native paste.
```

`computer{action:"key", text:"v", modifiers:"cmd"}` does **not** paste — it types a
literal `v` into the composer. That difference is the entire problem.

### Four routes that are DEAD — do not retry them
| Route | Result |
|---|---|
| `file_upload` tool | rejects project paths, scratchpad paths, and still rejects after `request_directory` grants the folder |
| `fetch('http://127.0.0.1:…')` from the page | grok.com CSP `connect-src` blocks it — nothing reaches the server |
| `<img src="http://127.0.0.1:…">` + canvas | grok.com CSP `img-src` blocks it too |
| `navigator.clipboard.read()` | hangs the renderer until the 45 s CDP timeout |

A synthetic `ClipboardEvent('paste')` carrying a `File` **does** work (Grok's handler
consumes it, `dispatchEvent` returns `false`) — but you still need the bytes in the
page, and the only way in is inlining ~1.48 M base64 chars per seed. Not sustainable
for 23 seeds. The osascript + `cmd+v` chord is the answer.

## Verify before submitting (each of these caught something)
1. **Zoom-verify the seed attached** — but the thumbnail is ~20 px, too small to read.
   Check it programmatically instead: the attached `blob:` `<img>` must report
   `naturalWidth/Height = 1264x720`. A text-only submit is otherwise silent.
2. **Prompt landed byte-exact** — composer is `contenteditable`; insert with
   `document.execCommand('insertText', false, PROMPT)` after `selectAll`+`delete`,
   then assert `ed.innerText.length === PROMPT.length`.
3. **720p + 6s selected.** The `16:9` pill *disappears* once an image is attached —
   that is correct, aspect ratio is inherited from the 1264x720 seed.

## Downloading — the URL is deterministic
After submit the URL becomes `/imagine/post/<UUID>`. The finished video is the one
`<video>` whose `src` contains that same `<UUID>`:
`assets.grok.com/users/<user>/generated/<UUID>/generated_video.mp4`.
Everything else on the page is sidebar history — do not grab those.

```js
const postId = location.pathname.split('/post/')[1].split('?')[0];
const v = [...document.querySelectorAll('video')].map(x=>x.src).find(s=>s.includes(postId));
const buf = await (await fetch(v,{credentials:'include'})).arrayBuffer();
// -> Blob -> <a download> ; lands in ~/Downloads via Chrome's download pipe
```
Output is 1264x720, 6.041667 s. Strip clip audio (`-an`) at assembly.

## Then frame-strip — mandatory, and it earns its keep
```bash
venv/bin/python research/wildbirdsurvival_teardown/make_clip_strip.py S002
```
3x3, 9 frames, timestamped. The very first clip generated this session **failed** on
its strip while looking fine in motion — see below.

## Track with the ledger, never by memory
```bash
venv/bin/python research/wildbirdsurvival_teardown/gen_clip_ledger.py --next 3   # status + next shots w/ prompts
venv/bin/python research/wildbirdsurvival_teardown/gen_clip_ledger.py --qa       # audit clips on disk
```
A shot counts as done only when BOTH `<ID>.mp4` and `<ID>_strip.jpg` exist, so a
clip whose strip was never reviewed is reported as unfinished on purpose.

---

# ⚠️ THE REAL LESSON FROM CLIP ONE: check the SEED, not just the prompt

**S002 take 1 was generated correctly and still had to be rejected**
(`clips/rejected/S002_take1*`). The prompt was byte-exact, 720p/6s were right, the
seed attached. It failed anyway, and **every failure traced to the seed, not the prompt**:

| Spec said | Seed `hero_still_A2_macro_finch_wound.png` actually is | Result |
|---|---|---|
| "extreme macro from high behind the finch's shoulder, angled steeply down the beak" | a side-on **medium** of the whole finch | wrong vantage — unreachable |
| "one finch only" | already contains **two** finches | second finch in shot |
| DRY stain that must not run | already shows a **slight downward red run** below the mark | Grok extended it into a streak running down the feathers by 4.4–5.7 s |

**Because Grok i2v begins on the seed's frame 1, no prompt wording can overrule the
seed's composition.** The DRY-blood rider cannot hold a stain still when the seed
itself already depicts it running.

### So, before generating any shot, check its seed against its prompt:
1. Open the seed PNG and look at it.
2. Does the **framing** match the prompt's stated shot size / camera position?
3. Does the **creature count** match ("one finch only" vs a seed with two)?
4. For blood shots: is the stain in the seed **already dry and compact**, or does it
   drip? A dripping seed will animate into a thread no matter what the rider says.

If any answer is no, fix the seed (crop it, or generate a new one) — do not burn a
generation on a prompt the seed cannot reach.

## Known seed-capability problems still open
- **S002** — as above. Needs either a true macro seed (a tight crop of the existing
  still, high-behind-the-shoulder, one finch, stain dry) or a re-spec of the shot to
  what this seed can actually deliver.
- **S021** — `still_booby_eye.png` is an extreme eye close-up with no neck, shoulder
  or sky in it; the shot asks for a low front-quarter looking **up at head and neck
  against flat sky** while the booby cranes its bill back over its shoulder. Not
  reachable from that seed.
- **S001 prompt drift (cosmetic, already resolved in practice).** S001's `vantage`
  says the head fills the **left** two-thirds with a soft finch in the right third —
  which is exactly what the seed shows and what the adopted clip does. Its
  `grok_prompt` says the **right** two-thirds and "one booby and one fly throughout"
  (no finch). The adopted clip follows the vantage and looks right, so S001 is done;
  but if it is ever regenerated, use the vantage, not the prompt.

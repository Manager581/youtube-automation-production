# EP02 — the Grok i2v grind: the working recipe

_Written 2026-07-23 after proving one clip end-to-end. Every step below was executed, not assumed._

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

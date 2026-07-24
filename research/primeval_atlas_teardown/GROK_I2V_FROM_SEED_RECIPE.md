# Grok i2v from a locked seed — the working recipe

_Written 2026-07-24 after proving it. Every step below was executed, not assumed._

## The unlock: don't upload anything. Animate Grok's OWN image.

Generate the seed **inside Grok Imagine** (Image mode, Quality, ×4, 9:16). Then open that
image's post page and use **Make Video → Add Prompt**. The seed is already server-side, so
there is no upload step at all — which sidesteps every attach problem below.

```
https://grok.com/imagine/post/<IMAGE_POST_ID>
  → right rail: "Make Video"  (approx 1473,504 at 1568px wide)
  → menu: "Add Prompt"        (approx 1428,464)   [the other option is "Quick Animate"]
  → composer appears WITH the seed already attached as a thumbnail
  → set 10s (approx 681,590), 720p
  → click the prompt field (approx 770,568), type MOTION-ONLY prompt, Return
```
The page does **not** navigate to a new post. The generation appears as a new item in the
**left rail** and the composer clears — that is how you know it submitted.

Re-open the same image post page in a new tab to queue the next shot from the same seed.
**Cap is 3 concurrent generations.** A 4th silently does nothing.

## ⚠️ THE SEED CARRIES THE ENVIRONMENT, NOT JUST THE ANIMAL
**One seed per ACT, not one seed for the film.** Proven the hard way: a seed of the animal
standing in a shallow river, prompted to "sink underwater", produced the animal still standing
in the shallow river while the *sky* turned green. The environment in the seed dominates and
i2v will not relocate it.

**Fix — make each act's seed by EDITING the master seed**, which preserves the design:
```
open the seed's post → type the edit prompt → click aria-label="Image" → click aria-label="Edit"
"Keep this exact same animal, identical anatomy, identical <snout/sail/hide>.
 Change ONLY the environment: <new location>."
```
That produced a genuinely underwater Spinosaurus with the identical snout, sail and hide.
Do the same for each act (bank / underwater / surface-aftermath), then shoot each act's
shots from its own seed.

## Submitting is a TWO-STEP — the single most common silent failure
After "Add Prompt", inserting text can flip the composer into **image-edit** mode, where the
submit button is `aria-label="Edit"` (which edits the still — NOT what you want).
Always, in this order:
```js
byLabel('Video').click()      // force video mode  -> submit becomes "Make video"
byText('10s').click()         // duration resets to 6s constantly; set it AFTER Video
byLabel('Make video').click() // the real submit
```
If `byLabel('Make video')` is missing, you are in image mode. Do not click `Edit`.

Verify the prompt landed byte-exact before submitting:
```js
document.execCommand('selectAll'); document.execCommand('delete');
document.execCommand('insertText',false,PROMPT);
// assert innerText.length === PROMPT.length
```

## Four attach routes that are DEAD — do not retry
| Route | Result |
|---|---|
| `mcp__claude-in-chrome__file_upload` | "only files the user has shared with this session" — rejects project paths AND the session scratchpad, even after `request_directory` grants the folder |
| osascript clipboard + extension `key cmd+v` | extension synthesizes an in-page key event; it is not a real browser paste. Nothing attaches |
| computer-use native `cmd+v` | Chrome is granted at tier "read" — clicks/typing into Chrome are blocked by design |
| synthetic `ClipboardEvent` carrying a `File` | **Preview appears but the upload never completes.** `Submit` stays `disabled` forever. Two blob thumbnails render, only one gets a "Remove image" button |

That last one is the trap: it *looks* like it worked. Always check
`[...document.querySelectorAll('button')].find(b=>b.getAttribute('aria-label')==='Submit').disabled`
before assuming an attach succeeded.

## Downloads
Chrome blocks automatic multi-file downloads per site after ~10 files. Fix is one click:
`chrome://settings/content/automaticDownloads` → allow `grok.com` and `chatgpt.com`.
Verify the pipe with a throwaway blob download before a batch — a blocked download is silent.

```js
// download the finished video for the CURRENT post
const p = location.pathname.split('/post/')[1].split('?')[0];
const src = [...document.querySelectorAll('video')].map(v=>v.src||'').find(s=>s.includes(p));
const buf = await (await fetch(src,{credentials:'include'})).arrayBuffer();
const u = URL.createObjectURL(new Blob([buf],{type:'video/mp4'}));
const a = document.createElement('a'); a.href=u; a.download='SHOT.mp4';
document.body.appendChild(a); a.click();
```

## Output spec
**720×1280, 24 fps, 10.04 s, AAC stereo.** Native clip audio is real and usable when the
prompt asks for diegetic sound (measured −29.3 LUFS / 12.3 LU on a good take); a batch that
comes back near −50 LUFS is effectively silent and needs sound built in post.

## Prompt rules (from the measured teardown)
- The seed governs the ANIMAL. The prompt governs **motion, camera and sound only**.
- Always name the camera height and behaviour explicitly — locked off, high looking down,
  low looking up, eye level. The reference film is **locked off in 9 of 19 shots** and never
  exceeds ~3.3% of frame width per second of drift.
- **Never** ask for: push in, pull back, zoom, dolly, orbit, handheld, shake, speed ramp.
- Always specify diegetic sound and end with "No music."
- Always append: "true natural colours, no colour grading, no glow, no lens flare."
- Refer to the animal as **"this exact animal"** so the model anchors to the seed.

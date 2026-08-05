#!/usr/bin/env python3
"""Photorealistic render pipeline for mine-site proposal visuals.

Takes the site floor plan + reference photos from inputs/ and generates
photoreal concept shots via an image-generation API.

Providers (auto-detected from environment):
  GEMINI_API_KEY  -> Google Gemini image model (default: gemini-2.5-flash-image),
                     multi-image input grounds the render in the real plan/photos.
  OPENAI_API_KEY  -> OpenAI gpt-image-1 (image edit endpoint with references).

Usage:
  python3 generate_renders.py --dry-run          # print shot prompts, no API calls
  python3 generate_renders.py --chatgpt-kit      # write chatgpt-prompts.md (no API)
  python3 generate_renders.py                    # generate all shots -> ../renders/
  python3 generate_renders.py --shot entrance    # generate one shot
  python3 generate_renders.py --config other_site.json   # another of the 11 sites
"""

import argparse
import base64
import json
import mimetypes
import os
import pathlib
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
INPUTS = HERE / "inputs"
RENDERS = HERE.parent / "renders"

GEMINI_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

# Which reference images ground each shot (order matters: plan first).
SHOTS = {
    "overview": {
        "title": "Isometric dollhouse overview",
        "refs": ["floor-plan.png", "chatgpt-attempt.png", "coveralls-interior.png"],
        "prompt": (
            "Create a photorealistic 3D isometric cutaway 'dollhouse' rendering of this mine dry "
            "facility, viewed from above at a 3/4 angle, matching the attached floor plan EXACTLY — "
            "same room positions, same hallways, same fixtures. The second attached image is a rough "
            "previous attempt: keep its camera style but greatly improve realism, lighting and color. "
            "The third attached photo shows the real orange coveralls to replicate on the racks.\n\n{scene}\n\n"
            "Render at high quality: soft studio lighting, realistic shadows, {style}"
        ),
    },
    "entrance": {
        "title": "Eye-level view walking in the main doors",
        "refs": ["floor-plan.png", "coveralls-interior.png", "crew-coveralls.png"],
        "prompt": (
            "Create a photorealistic eye-level interior rendering standing just inside the main "
            "entrance (black-framed glass double doors behind the camera), looking into the mine dry "
            "facility described below and laid out in the attached floor plan. Dark safety mats in the "
            "foreground, the long rack of orange hi-vis coveralls along the left wall — matching the "
            "attached reference photos of the real coveralls — drying rails with hanging orange "
            "coveralls in the middle distance, and the two color-coded hallway entrances on the right.\n\n"
            "{scene}\n\nWide-angle interior photograph look, realistic materials and lighting, {style}"
        ),
    },
    "hallway": {
        "title": "Hallway with vending, looking toward change rooms",
        "refs": ["floor-plan.png"],
        "prompt": (
            "Create a photorealistic eye-level interior rendering looking down a 7-foot-wide hallway "
            "in the mine dry facility from the attached floor plan: a modern vending machine on the "
            "left wall at the hallway entrance, doors to a change room and bathrooms on the right, "
            "clean painted concrete-block walls with a yellow accent stripe, sealed concrete floor.\n\n"
            "{scene}\n\nRealistic interior photograph look, {style}"
        ),
    },
    "innovation-hub": {
        "title": "TV innovation hub feature shot",
        "refs": ["floor-plan.png", "crew-coveralls.png"],
        "prompt": (
            "Create a photorealistic feature rendering of the proposed 'TV Innovation Hub' inside the "
            "mine dry facility from the attached floor plan: a freestanding navy media wall with a "
            "large mounted TV showing a clean safety-metrics dashboard, two modern stools in front, "
            "positioned where the open dry area meets the rest of the building; orange coveralls on "
            "racks softly out of focus in the background.\n\n{scene}\n\n"
            "Professional interior-design visualization look, shallow depth of field, {style}"
        ),
    },
    "micro-market": {
        "title": "Micro-market vending feature shot",
        "refs": ["floor-plan.png"],
        "prompt": (
            "Create a photorealistic feature rendering of the proposed micro-market zone near the main "
            "entrance of the mine dry facility from the attached floor plan: two modern glass-front "
            "smart-vending units stocked with PPE consumables (gloves, ear plugs, safety glasses) and "
            "snacks, on a dedicated floor zone, with the glass double-door entrance and dark safety "
            "mats visible nearby.\n\n{scene}\n\nRealistic interior photograph look, {style}"
        ),
    },
}


def build_scene(cfg):
    lines = [cfg["client_context"], cfg["footprint"], "Layout:"]
    lines += [f"- {item}" for item in cfg["layout"]]
    lines.append("Proposed innovations to include:")
    lines += [f"- {i['name']}: {i['description']}" for i in cfg["innovations"]]
    return "\n".join(lines)


def load_refs(names):
    out = []
    for n in names:
        p = INPUTS / n
        if not p.exists():
            sys.exit(f"missing reference image: {p}")
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        out.append((mime, p.read_bytes()))
    return out


def call_gemini(key, prompt, refs):
    parts = [{"text": prompt}]
    for mime, data in refs:
        parts.append({"inline_data": {"mime_type": mime,
                                      "data": base64.b64encode(data).decode()}})
    body = json.dumps({
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.load(r)
    for part in resp["candidates"][0]["content"]["parts"]:
        blob = part.get("inlineData") or part.get("inline_data")
        if blob:
            return base64.b64decode(blob["data"])
    raise RuntimeError(f"no image in Gemini response: {json.dumps(resp)[:600]}")


def call_openai(key, prompt, refs):
    # gpt-image-1 edits endpoint accepts reference images as multipart form data.
    boundary = "----pipeline-boundary-7f3a"
    parts = []

    def field(name, value):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; "
                     f'name="{name}"\r\n\r\n{value}\r\n'.encode())

    field("model", "gpt-image-1")
    field("prompt", prompt[:31900])
    field("size", "1536x1024")
    for i, (mime, data) in enumerate(refs):
        ext = "png" if "png" in mime else "jpg"
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"image[]\"; "
            f"filename=\"ref{i}.{ext}\"\r\nContent-Type: {mime}\r\n\r\n".encode()
            + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/edits",
        data=b"".join(parts),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.load(r)
    return base64.b64decode(resp["data"][0]["b64_json"])


def write_chatgpt_kit(cfg, scene, path):
    """Write the shot prompts as a copy-paste kit for ChatGPT (no API needed)."""
    lines = [
        f"# ChatGPT Render Kit — {cfg['site_name']}",
        "",
        "How to use: for each shot below, start a fresh ChatGPT message, **attach the",
        "listed images** (they're in `pipeline/inputs/`), paste the prompt, and send.",
        "Ask for landscape/wide format if it comes back square. If a detail is off,",
        "reply with a correction (\"make the coveralls brighter orange\", \"the vending",
        "machine goes at the hallway entrance\") — iterating in the same chat keeps",
        "the layout consistent.",
        "",
    ]
    for name, shot in SHOTS.items():
        prompt = shot["prompt"].format(scene=scene, style=cfg["style"])
        lines += [
            f"## {name} — {shot['title']}",
            "",
            "**Attach:** " + ", ".join(f"`{r}`" for r in shot["refs"]),
            "",
            "```",
            prompt,
            "```",
            "",
        ]
    pathlib.Path(path).write_text("\n".join(lines))
    print(f"wrote {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print prompts, no API calls")
    ap.add_argument("--chatgpt-kit", action="store_true",
                    help="write chatgpt-prompts.md for manual use in ChatGPT (no API)")
    ap.add_argument("--shot", choices=sorted(SHOTS), help="generate a single shot")
    ap.add_argument("--config", default=str(HERE / "site_config.json"),
                    help="site config JSON (default: site_config.json)")
    args = ap.parse_args()

    cfg = json.loads(pathlib.Path(args.config).read_text())
    scene = build_scene(cfg)
    if args.chatgpt_kit:
        write_chatgpt_kit(cfg, scene, HERE / "chatgpt-prompts.md")
        return
    shots = {args.shot: SHOTS[args.shot]} if args.shot else SHOTS

    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not args.dry_run and not (gemini_key or openai_key):
        sys.exit("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY "
                 "(or use --dry-run to preview prompts).")

    provider = "gemini" if gemini_key else ("openai" if openai_key else None)
    print(f"site: {cfg['site_name']}")
    print(f"provider: {provider or 'none (dry run)'}\n")

    RENDERS.mkdir(exist_ok=True)
    for name, shot in shots.items():
        prompt = shot["prompt"].format(scene=scene, style=cfg["style"])
        refs = load_refs(shot["refs"])
        print(f"=== {name}: {shot['title']}")
        print(f"    refs: {', '.join(shot['refs'])}")
        if args.dry_run:
            print("    prompt:")
            for line in prompt.splitlines():
                print(f"      {line}")
            print()
            continue
        try:
            png = (call_gemini(gemini_key, prompt, refs) if provider == "gemini"
                   else call_openai(openai_key, prompt, refs))
        except urllib.error.HTTPError as e:
            print(f"    ERROR {e.code}: {e.read().decode()[:500]}")
            continue
        out = RENDERS / f"{name}.png"
        out.write_bytes(png)
        print(f"    wrote {out} ({len(png) // 1024} KB)")


if __name__ == "__main__":
    main()

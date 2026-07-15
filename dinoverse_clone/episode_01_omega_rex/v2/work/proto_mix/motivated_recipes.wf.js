export const meta = {
  name: 'dinoverse-motivated-recipes',
  description: 'Per-clip motivated cut recipe for every body shot (look at frames, read line, aim-verify)',
  phases: [{ title: 'Recipe', detail: 'one agent per body clip; motivated trim + punch/hold with aim check' }],
}

const CL = '/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/clips'
const PM = '/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/v2/work/proto_mix'
const PY = '/Users/jefflawrence/Documents/youtube-automation-production/venv/bin/python'
const OUT = `${PM}/_recipe_frames`

const SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['shot', 'shot_type', 'technique', 'trim_end', 'cut_at', 'zoom', 'xp', 'yp', 'aim_ok', 'rationale'],
  properties: {
    shot: { type: 'string' },
    shot_type: { type: 'string', description: 'establishing / wide / medium / close-up / two-shot / POV / impact / action / detail' },
    technique: { type: 'string', enum: ['hold', 'punch'] },
    trim_end: { type: 'number', description: 'seconds where the clip ends (>= speech_end, <= clip_dur). Trim dead tail.' },
    cut_at: { type: 'number', description: 'punch only: the pause time to cut to the push. 0 if hold.' },
    zoom: { type: 'number', description: 'punch only: 1.15-1.40. 1.0 if hold.' },
    xp: { type: 'number', description: 'punch target center X fraction 0..1 from the CUT-POINT frame. 0.5 if hold.' },
    yp: { type: 'number', description: 'punch target center Y fraction 0..1. 0.5 if hold.' },
    aim_ok: { type: 'boolean', description: 'true only if you extracted the punch crop and CONFIRMED the subject is inside it' },
    rationale: { type: 'string', description: 'one line: why this cut, tied to the line + what is on screen' },
  },
}

const shots = typeof args === 'string' ? JSON.parse(args) : args
phase('Recipe')

const recipes = await parallel(shots.map(shot => () => agent(
`You are a video editor making ONE motivated cut decision for a single shot. NOT a formula — the cut must be justified by what is on screen + what the line says. You can SEE images with the Read tool.

SHOT: ${shot}   CLIP: ${CL}/${shot}.mp4

STEP 0 — get this clip's data:
  ${PY} -c "import json;d={c['shot']:c for c in json.load(open('${PM}/recipe_args.json'))['clips']}['${shot}'];print('dur',d['clip_dur'],'| speech_end',d['speech_end'],'| pauses',d['pauses'],'| speaker',d['speaker'],'| beat',d['beat'],'| camera',d['camera']);print('LINE:',d['text'])"
Read the line, speaker, beat, pauses, and speech_end.

RULES:
1) TRIM: trim_end = speech_end + ~0.3s (drop dead air where nobody talks). Never below speech_end. If speech fills the clip (speech_end within ~0.4s of dur) OR this is a deliberate HOLD beat (beat mentions a long money-shot / reveal / roar / show, or the clip is 10s), keep trim_end = clip_dur.
   NOTE: silent clips (speech_end 0, empty line) are action beats — HOLD full, no punch.

2) LOOK before deciding:
  mkdir -p ${OUT}
  ffmpeg -y -v error -i ${CL}/${shot}.mp4 -vf "fps=1,scale=400:-1,tile=3x2" -frames:v 1 ${OUT}/${shot}_grid.png
  Read it. Identify shot_type, who/what is in frame, and WHERE.

3) DECIDE — motivated, not default:
  - HOLD (no punch) for: establishers (gate/sign/entrance), already-tight close-ups & impact shots, deliberate money-shots/reveals/roars, POV with no clear push target, or a composition that IS the joke/point. Holds give rhythm contrast — do NOT punch everything. Roughly half should be holds.
  - PUNCH for a real motivated target: a REACTION (cut to the person reacting on their beat), an ATTENTION cue in the line ("look at...", naming a feature), or subject/CTA emphasis. cut_at = a pause AT/just before that beat.

4) If PUNCH, aim from the CUT-POINT frame (subjects move across the clip!):
  ffmpeg -y -v error -ss <cut_at> -i ${CL}/${shot}.mp4 -frames:v 1 -vf scale=600:-1 ${OUT}/${shot}_cut.png ; Read it. Set xp,yp = your target's CENTER fraction in THAT frame; zoom 1.2-1.35.
  VERIFY the aim:
  ffmpeg -y -v error -ss <cut_at> -i ${CL}/${shot}.mp4 -frames:v 1 -vf "scale=iw*<zoom>:ih*<zoom>,crop=iw/<zoom>:ih/<zoom>:(iw*<zoom>)*<xp>-iw/2:(ih*<zoom>)*<yp>-ih/2" ${OUT}/${shot}_aim.png ; Read it.
  If the subject is NOT well inside the crop, adjust xp/yp and re-check. aim_ok=true only when correct. If no good punch exists, fall back to HOLD.

Return the recipe. Ranges: trim_end in [speech_end, clip_dur]; cut_at a real pause with 0.5 < cut_at < trim_end-0.6; xp,yp in 0.15..0.85; zoom 1.15..1.4. rationale = one line tying the cut to the line + frame.`,
  { label: `recipe:${shot}`, phase: 'Recipe', schema: SCHEMA }
)))

return { recipes: recipes.filter(Boolean) }

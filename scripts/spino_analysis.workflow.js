export const meta = {
  name: 'spinosnack-analysis',
  description: 'Deep top-vs-bottom-vs-recent analysis of Spinosnack videos to extract the winning formula',
  phases: [
    { title: 'Analyze', detail: 'one analyst agent per video (visuals + audio + script + thumbnail)' },
    { title: 'Synthesize', detail: 'cross-pattern synthesis -> build spec' },
  ],
}

// 13-video work-list (top5/bottom5/recent3, age-normalized by views/day), embedded
// directly so the run doesn't depend on args passing (workflow scripts can't read files).
const videos = [
  {id:"xQbYQQjWR2k",title:"I Simulated Megalodon In the Modern Ocean, Chaos Followed",bucket:"top",views:1831548,viewsPerDay:22611.7,date:"20260320",durationSec:1121},
  {id:"cBi6AUtVl04",title:"I Simulated A Titanoboa In The Modern Amazon, Chaos Followed",bucket:"top",views:1585564,viewsPerDay:22021.7,date:"20260329",durationSec:1595},
  {id:"FcAns8s3Kiw",title:"The Deeper You Go, The Creepier Prehistoric Oceans Get",bucket:"top",views:5154094,viewsPerDay:17772.7,date:"20250823",durationSec:1560},
  {id:"DzUKhb2ZSko",title:"I Simulated A T.Rex In Modern Africa, Chaos Followed",bucket:"top",views:1248697,viewsPerDay:16874.3,date:"20260327",durationSec:1726},
  {id:"zW7RTQqgQB0",title:"How It Feels Like To Die In Every Prehistoric Era",bucket:"top",views:1827051,viewsPerDay:14616.4,date:"20260204",durationSec:1609},
  {id:"llPh0Oyo--0",title:"No Dinosaur EVER Reached A Blue Whale's Size, But Why?",bucket:"bottom",views:23855,viewsPerDay:106.5,date:"20251028",durationSec:1129},
  {id:"HmfE_nb8rJE",title:"Why These Movie Flying Dinosaurs Are Pure Nightmare Fuel",bucket:"bottom",views:36083,viewsPerDay:100.2,date:"20250614",durationSec:1236},
  {id:"SbO0p2WapIc",title:"Could the D Rex Actually SURVIVE the Cretaceous?",bucket:"bottom",views:13919,viewsPerDay:45.0,date:"20250804",durationSec:911},
  {id:"fYOPtdxapmE",title:"How Long Would the D Rex Last in the REAL Triassic?",bucket:"bottom",views:13326,viewsPerDay:42.0,date:"20250727",durationSec:823},
  {id:"wmWojCWnyas",title:"Why These Movie T. Rexes Are Pure Nightmare Fuel Killers",bucket:"bottom",views:11156,viewsPerDay:31.7,date:"20250622",durationSec:1109},
  {id:"qPZUCU6XnTQ",title:"The Deeper You Look Into Amber, The Stranger It Gets",bucket:"recent",views:443107,viewsPerDay:15825.2,date:"20260512",durationSec:1234},
  {id:"Jg_bcpOvoa0",title:"I Simulated 1000 Megalodons In the Modern Ocean, Chaos Followed",bucket:"recent",views:110125,viewsPerDay:15732.1,date:"20260602",durationSec:958},
  {id:"9Wtnz1NQdxM",title:"What Happens if You Drop Spinosaurus Into The Florida Everglades?",bucket:"recent",views:1228117,viewsPerDay:13955.9,date:"20260313",durationSec:1561},
]

const YTDLP = '/Users/jefflawrence/miniforge3/bin/yt-dlp'
const PY = '/Users/jefflawrence/Documents/youtube-automation-production/venv/bin/python'

const VIDEO_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['id','title','bucket','format','topic','hook','script','visuals','audio','whyHypothesis'],
  properties: {
    id: { type: 'string' }, title: { type: 'string' }, bucket: { type: 'string' },
    format: { type: 'string', description: 'e.g. POV "I Simulated", "Deeper You Go" exploratory, listicle, essay' },
    topic: { type: 'string' },
    thumbnail: { type: 'object', additionalProperties: false, properties: {
      text: { type: 'string' }, subject: { type: 'string' }, colors: { type: 'string' }, tactic: { type: 'string' } } },
    hook: { type: 'object', additionalProperties: false,
      required: ['first15s','killerStatOpen','openLoop'], properties: {
      first15s: { type: 'string' }, killerStatOpen: { type: 'boolean' },
      povFlipSec: { type: ['number','null'] }, openLoop: { type: 'boolean' } } },
    script: { type: 'object', additionalProperties: false,
      required: ['wpm','povSecondPerson','cta','structureNotes'], properties: {
      wpm: { type: 'number' }, povSecondPerson: { type: 'boolean' },
      openLoops: { type: 'boolean' }, cta: { type: 'string' }, structureNotes: { type: 'string' } } },
    visuals: { type: 'object', additionalProperties: false,
      required: ['cutRateSec','motionPct','treatments','textOverlays','colorGrade'], properties: {
      cutRateSec: { type: 'number' }, motionPct: { type: 'number' },
      treatments: { type: 'array', items: { type: 'string' } },
      usesCirclesOrMotionGfx: { type: 'boolean' }, textOverlays: { type: 'boolean' },
      colorGrade: { type: 'string' }, hookVisualNotes: { type: 'string' } } },
    audio: { type: 'object', additionalProperties: false,
      required: ['musicBed','deliveryNotes'], properties: {
      musicBed: { type: 'boolean' }, sfxDensityPerMin: { type: ['number','null'] },
      deliveryNotes: { type: 'string' } } },
    standoutTactics: { type: 'array', items: { type: 'string' } },
    whyHypothesis: { type: 'string', description: 'why this likely landed in its bucket (top/bottom/recent)' },
  },
}

function analystPrompt(v) {
  const dir = `/tmp/spino_wf/${v.id}`
  return `You are a YouTube format analyst. Analyze ONE Spinosnack video with REAL evidence (download + measure + LOOK at frames). Do NOT guess — every field must come from a tool result or a frame you actually viewed.

VIDEO: id=${v.id} | title=${JSON.stringify(v.title)} | bucket=${v.bucket} | views=${v.views} | views/day=${v.viewsPerDay} | duration=${v.durationSec}s

Tools/paths (use EXACTLY these):
- yt-dlp: ${YTDLP}
- ffmpeg / ffprobe: in PATH
- python (numpy, PIL, librosa, whisper available): ${PY}

STEPS (run them; tolerate failures and continue with partial data):
1. mkdir -p ${dir} && cd ${dir}
2. Thumbnail: ${YTDLP} --skip-download --write-thumbnail --convert-thumbnails jpg -o "${dir}/thumb.%(ext)s" "https://www.youtube.com/watch?v=${v.id}" ; then READ ${dir}/thumb.jpg and describe text/subject/colors/click-tactic.
3. Full transcript: ${YTDLP} --skip-download --write-auto-sub --sub-lang en --sub-format vtt -o "${dir}/subs.%(ext)s" "https://www.youtube.com/watch?v=${v.id}" . Parse subs.en.vtt: dedup rolling captions; analyze the HOOK (first 30s with timestamps), whether it opens on a killer stat, whether/when it flips to 2nd-person POV ("you are/you hatch"), open loops ("remember that"), the CTA at the end, and estimate WPM (words / video-minutes).
4. Visual sample: ${YTDLP} -f "bv*[height<=480]+ba/b[height<=480]/b" --download-sections "*00:00-03:00" -o "${dir}/clip.%(ext)s" --force-overwrites "https://www.youtube.com/watch?v=${v.id}" . The file is ${dir}/clip.webm (or .mp4).
5. Cut rate: ffmpeg -i <clip> -filter:v "select='gt(scene,0.3)',showinfo" -an -f null - 2>&1 | grep -oE "pts_time:[0-9.]+" | wc -l  -> cuts over 180s -> cutRateSec = 180/cuts.
6. Motion %: ${PY} -c "import numpy as np,glob,subprocess,os;from PIL import Image;subprocess.run(['ffmpeg','-y','-i','<clip>','-vf','fps=3,scale=160:90','${dir}/mf_%04d.jpg'],capture_output=True);fs=sorted(glob.glob('${dir}/mf_*.jpg'));a=[np.asarray(Image.open(f).convert('L'),np.float32) for f in fs];d=[float(np.mean(np.abs(a[i]-a[i-1]))) for i in range(1,len(a))];print('motionPct',round(100*sum(x>3 for x in d)/max(1,len(d))))"
7. Audio/SFX: ffmpeg -y -i <clip> -t 120 -ar 22050 -ac 1 ${dir}/au.wav ; ${PY} -c "import librosa;y,sr=librosa.load('${dir}/au.wav',sr=22050);on=librosa.onset.onset_detect(y=librosa.effects.percussive(y),sr=sr,units='time');print('sfxPerMin',round(len(on)/2))" (treat as proxy; note continuous music bed if present).
8. Treatments: extract ~9 frames across the 3-min clip (ffmpeg -ss <t> -i <clip> -frames:v 1 ${dir}/f_<t>.jpg for t in 5 20 40 60 90 120 150 170), READ 6-8 of them, and catalog the visual treatments you SEE: AI image-to-video, 3D render, real stock footage, vintage engraving/illustration, animated photo-cards, motion-graphics/circles/rings/arrows, bold stat-text overlays, color grade (e.g. teal/blue), particles/god-rays. Record usesCirclesOrMotionGfx and textOverlays as booleans based on what you actually saw.

Then return the structured object. Be concrete and quantitative. format/topic from the title+content. whyHypothesis = your evidence-based reason this is a ${v.bucket} performer.`
}

phase('Analyze')
log(`Analyzing ${videos.length} videos: ${videos.filter(v=>v.bucket==='top').length} top, ${videos.filter(v=>v.bucket==='bottom').length} bottom, ${videos.filter(v=>v.bucket==='recent').length} recent`)
const analyses = (await parallel(videos.map(v => () =>
  agent(analystPrompt(v), { label: `analyze:${v.bucket}:${v.id}`, phase: 'Analyze', schema: VIDEO_SCHEMA })
))).filter(Boolean)
log(`Got ${analyses.length}/${videos.length} analyses back`)

phase('Synthesize')
const REPORT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['consistentDNA','topVsBottom','formatPerformance','titleThumbnailPatterns','scriptPatterns','visualAudioPatterns','currentTrends','buildSpec','topTakeaways'],
  properties: {
    consistentDNA: { type: 'array', items: { type: 'string' }, description: 'what EVERY video does regardless of performance' },
    topVsBottom: { type: 'array', items: { type: 'string' }, description: 'concrete differences separating top from bottom performers' },
    formatPerformance: { type: 'array', items: { type: 'object', additionalProperties: true } },
    titleThumbnailPatterns: { type: 'array', items: { type: 'string' } },
    scriptPatterns: { type: 'array', items: { type: 'string' } },
    visualAudioPatterns: { type: 'array', items: { type: 'string' } },
    currentTrends: { type: 'array', items: { type: 'string' }, description: 'what recent (last 3 mo) videos do differently' },
    buildSpec: { type: 'object', additionalProperties: true, description: 'actionable spec: title, thumbnail, hook, script, visuals, audio, edit' },
    topTakeaways: { type: 'array', items: { type: 'string' } },
  },
}
const report = await agent(
  `You are a YouTube strategist. Below are structured analyses of Spinosnack videos, tagged bucket=top|bottom|recent (top/bottom by views-per-day over the last year; recent = best of last 3 months). Find the PATTERNS that separate winners from losers and produce an actionable build spec for recreating this channel's style.

Pay special attention to: what TOP performers share that BOTTOM lack (title, topic, thumbnail, hook, format, cut pace, duration, engagement); which FORMAT wins (POV "I Simulated" vs "Deeper You Go" vs listicle); what RECENT videos are changing (new visual styles, graphics); and the script architecture that correlates with success. Be specific and evidence-based; cite video ids.

DATA (JSON):
${JSON.stringify(analyses)}

Return the structured report.`,
  { label: 'synthesize', phase: 'Synthesize', schema: REPORT_SCHEMA }
)

return { analyses, report, counts: { requested: videos.length, analyzed: analyses.length } }

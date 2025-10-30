Software Design Spec — Podcast → Visual Video Factory (NotebookLM Deep-Dive Builder)
1) Goal (What this thing does)

Turn long-form audio (podcast / NotebookLM deep-dive) plus an optional transcript into a finished MP4:

Scene changes every N seconds (configurable).

Each scene shows a synthetic image generated via ComfyUI (Stable Diffusion backend) from an LLM-crafted prompt tied to that segment’s content.

Overlaid short, punchy captions (hooks), not karaoke.

Audio is the original track; video timing matches segment boundaries.

One-command CLI; deterministic by default.

2) Non-goals (for v1)

No web UI, no user accounts, no queue. (Those are Phase 3.)

No animated SD/video diffusion in v1 (still images only).

No dependency on any forum or external document.

3) High-level pipeline
Audio (+ optional SRT)
   └─► [A] Transcribe (if no SRT provided) → SRT
        └─► [B] Parse SRT → timestamped lines
             └─► [C] Segmenter → fixed N-second segments w/ text
                  └─► [D] LLM → per-segment {image_prompt, negative_prompt, caption}
                       └─► [E] ComfyUI → generate still image per segment
                            └─► [F] FFmpeg → assemble images + captions + audio → MP4

4) Project layout (single repo)
podcast-visual-factory/
├─ config.py                        # central configuration
├─ podcast_video_factory.py         # CLI orchestrator (entrypoint)
├─ core/
│  ├─ transcript_parser.py          # SRT read or Whisper transcription
│  ├─ segmenter.py                  # fixed-length segmentation
│  ├─ prompt_generator.py           # LLM calls, JSON out
│  ├─ comfy_client.py               # REST+WS client for ComfyUI
│  ├─ captions.py                   # build ASS subtitles from hooks
│  ├─ video_assembler.py            # FFmpeg wrapper
│  └─ logging_utils.py              # structured logs
├─ workflows/
│  └─ comfy_template.json           # minimal SDXL graph template (param placeholders)
├─ input/
│  └─ episode.*                     # .mp3/.wav and optional .srt
├─ output/
│  └─ {slug}/                       # segments.json, prompts.json, images/, final.mp4, logs/
├─ requirements.txt
└─ README.md

5) Dependencies

Python 3.10+

FFmpeg in PATH

ComfyUI running locally or remote (HTTP + WebSocket) with at least one SD checkpoint (e.g., SDXL).

LLM endpoint (OpenAI-compatible; can be OpenAI, local LM Studio, or your gateway).

Python packages (requirements.txt):

faster-whisper
requests
websocket-client

6) Configuration (config.py)

All runtime knobs live here. Coders must implement sane defaults.

# IO
AUDIO_PATH          = "input/episode.mp3"  # can be overridden via CLI
SRT_PATH            = None                 # if None → transcribe
OUTPUT_ROOT         = "output"             # will create output/{slug}/

# Segmentation
SEGMENT_SECONDS     = 12                   # fixed-length segments
MAX_SEG_TEXT_CHARS  = 900                  # truncate long transcripts per segment

# Captions (ASS)
CAPTION_MAX_CHARS   = 88
CAPTION_CASE        = "title"              # "title" | "sentence" | "none"
CAPTION_FONT        = "Arial"
CAPTION_FONTSIZE    = 42
CAPTION_MARGIN      = 60                   # px from bottom
CAPTION_STROKE      = 2                    # outline width
CAPTION_BG_ALPHA    = 0.35                 # 0..1 transparent box behind text

# LLM (OpenAI-compatible; can be local)
OPENAI_API_KEY      = "YOUR_KEY"
OPENAI_BASE_URL     = "https://api.openai.com/v1"  # or local gateway
OPENAI_MODEL        = "gpt-4o-mini"        # fast JSON output model

# Global visual style
GLOBAL_STYLE        = (
  "cinematic, sacred geometry, cosmic-tech elegance, crisp detail, "
  "clean composition, dramatic lighting, high dynamic range"
)
NEGATIVE_STYLE      = "blurry, watermark, text, logo, extra limbs, distorted, low-res"

# Image generation / ComfyUI
WIDTH               = 1920
HEIGHT              = 1080
SEED                = 123456
STEPS               = 30
CFG                 = 6.5
SAMPLER_NAME        = "euler"
SCHEDULER           = "normal"
BATCH_SIZE          = 1
COMFY_HOST          = "127.0.0.1"
COMFY_PORT          = 8188
COMFY_OUTPUT_DIR    = "output"   # Comfy save path (ensure writable)

# FFmpeg
FFMPEG_EXE          = "ffmpeg"
VIDEO_FPS           = 30
VIDEO_BITRATE       = "10M"

# Behaviour
ALLOW_REUSE         = True        # reuse existing segments/prompts/images
RETRY_LLM           = 3
RETRY_COMFY         = 2
TIMEOUT_COMFY_SEC   = 600

7) Data contracts (JSON files)
7.1 segments.json
[
  {"index":0,"start_ms":0,"end_ms":12000,"text":"Intro / setup ..." },
  {"index":1,"start_ms":12000,"end_ms":24000,"text":"Main idea A ..." }
]

7.2 prompts.json
{
  "global_style":"cinematic, sacred geometry, cosmic-tech elegance, crisp detail",
  "results":[
    {
      "segment_index":0,
      "seconds":12,
      "prompt":"(Segment-aware prompt here) [GLOBAL_STYLE inline]",
      "negative_prompt":"blurry, watermark, text, logo, extra limbs, distorted, low-res",
      "caption":"The idea in one sharp line"
    }
  ]
}

7.3 manifest.json
{
  "audio":"input/episode.mp3",
  "slug":"episode_2025-10-13",
  "output":"output/episode_2025-10-13/final.mp4",
  "segments":"segments.json",
  "prompts":"prompts.json",
  "images":[
    {"segment_index":0,"file":"images/seg_000.png","seed":123456}
  ],
  "video":{"fps":30,"bitrate":"10M","size":"1920x1080"}
}

8) Module specs (what to build)
8.1 transcript_parser.py

If SRT_PATH provided: parse into List[Line] where Line={start_ms,end_ms,text}.

Else transcribe:

Use faster_whisper model (e.g., large-v3) to produce SRT.

Save SRT next to audio; then parse to List[Line].

Normalise text (strip, collapse whitespace).

Output: List[Line] for downstream.

8.2 segmenter.py

Input: List[Line], SEGMENT_SECONDS.

Produce sequential segments [0..K-1]:

segment i: [i*N, (i+1)*N) seconds in ms.

Gather all transcript text overlapping this window; concatenate.

Truncate to MAX_SEG_TEXT_CHARS.

If final partial window < 3 seconds, merge into previous.

Output: List[Segment] and write segments.json.

8.3 prompt_generator.py

For all segments, make one LLM call using system+user prompt with response_format={"type":"json_object"} requesting a JSON object with results[ ] of:

segment_index, prompt, negative_prompt (default to NEGATIVE_STYLE if omitted), caption.

Prompt rules (must be enforced by the system prompt):

Do not include any literal text rendering in the image (“no words in image”).

Fold GLOBAL_STYLE into the positive prompt.

Captions: 6–12 words, not transcript quotes; punchy hooks.

Keep prompts safe (no disallowed content); abstract metaphors are fine.

Retries: up to RETRY_LLM with exponential backoff.

Write prompts.json.

System prompt snippet (coders must include and keep idempotent):

You are generating stable-diffusion prompts for video segments.
Rules:
- Incorporate the provided GLOBAL_STYLE into each prompt.
- Never include text/typography in the image. Avoid words, logos, watermarks.
- Negative prompt must discourage blur, artifacts, and unwanted text.
- Caption must be 6–12 words, human-hook style, not copied transcript.
Return strict JSON with the shape:
{
  "results": [
    {
      "segment_index": <int>,
      "prompt": "<positive prompt>",
      "negative_prompt": "<negative or global default>",
      "caption": "<short hook>"
    }, ...
  ]
}

8.4 comfy_client.py

Provide:

queue_prompt(graph_dict) -> prompt_id

wait_for_images(prompt_id, client_id, timeout_s) -> List[str]
(WS /ws?clientId=..., wait until execution_end; collect saved files.)

build_graph(prompt, negative, width, height, seed, steps, cfg, sampler, scheduler) -> dict
Use workflows/comfy_template.json as base; fill text/params.

Determinism: Seed per segment = SEED + segment_index.

If BATCH_SIZE > 1, generate multiple candidates; pick first (v1) and record all filenames in logs.

8.5 captions.py

Build an ASS subtitle file from prompts.json.results[].caption:

One event per segment: Start=(segment.start), End=(segment.end).

Style uses CAPTION_* variables; place near bottom, centred.

Enforce CAPTION_MAX_CHARS (truncate with ellipsis).

Casing rules: "title" → Title Case; "sentence" → Sentence case.

8.6 video_assembler.py

Put generated images as images/seg_000.png, seg_001.png, …

Create a concat list images_list.txt with explicit durations:

file 'images/seg_000.png'
duration 12
file 'images/seg_001.png'
duration 12
...
file 'images/seg_LAST.png'
duration LAST_DURATION


FFmpeg command (v1 hard cuts, subtitles burned in):

ffmpeg -y -f concat -safe 0 -i images_list.txt \
       -i "{AUDIO_PATH}" \
       -vf "subtitles=captions.ass:fontsdir=." \
       -r {VIDEO_FPS} -c:v libx264 -preset medium -b:v {VIDEO_BITRATE} -pix_fmt yuv420p \
       -c:a aac -b:a 192k "final.mp4"


Write manifest.json with all key params, file lists, and outputs.

8.7 podcast_video_factory.py (CLI)

Args override config.py:

--audio PATH
--srt PATH
--out DIR
--seg-sec N
--width W --height H
--fps FPS --bitrate BITRATE
--style "GLOBAL_STYLE override"
--force   # ignore ALLOW_REUSE and regenerate everything


Orchestration order:

Resolve slug + output folder.

Transcribe (if no SRT) → parse.

Segment → segments.json.

If reuse allowed and prompts.json exists, load; else generate via LLM.

For each segment:

Build Comfy graph → queue → wait for images → copy/chmod to images/.

Build captions.ass.

Assemble MP4 via FFmpeg.

Write manifest.json, summary log, exit 0.

8.8 logging_utils.py

Structured log file at output/{slug}/run.log (JSONL).

Include: step, timestamp, segment index, seeds, file paths, durations, errors.

9) Behavioural guarantees

Idempotent when ALLOW_REUSE=True: existing segments.json, prompts.json, and images are reused unless --force.

Deterministic across runs with same inputs+seed.

Graceful failure:

Missing ComfyUI → clear error: host/port/unreachable.

LLM JSON invalid → retry; on final fail, abort with actionable message.

FFmpeg missing → abort with message to install/adjust PATH.

10) Tests (acceptance)

With SRT present: Produces MP4 whose duration matches audio ±1s; correct image count equals segment count; captions render; exit 0.

Without SRT: Autotranscribes with faster_whisper, then passes Test 1.

Short audio (< SEGMENT_SECONDS): Single segment handled correctly.

Determinism: Same seed → byte-identical images and identical manifest.json (except timestamps).

Failure modes:

Kill ComfyUI → process aborts with clear error code/message.

Corrupt LLM JSON → retried up to RETRY_LLM, then aborts.

11) Performance notes

Image gen is the bottleneck. Parallelise with care:

At v1, sequential generation is acceptable.

Later: batch or concurrent generation limited by GPU VRAM.

FFmpeg does one pass; avoid re-encoding intermediates.

12) Phase 2 (polish queue)

Ken Burns pan/zoom per still (mild motion).

Semantic boundaries via LLM (variable segment length).

Chapter export (YouTube chapters from boundaries).

AnimateDiff for 2–3 hero segments.

Asset cache + style packs (consistent visuals across episodes).

Auto thumbnail + YT description + tags.

13) Phase 3 (service mode)

REST API + worker(s) + job queue (Celery/RQ).

Minimal React/HTML front end (upload audio, set style, generate).

Progress polling or WebSockets.

Embeddable via iframe (Discourse or anywhere else).

Storage lifecycle + pruning.

14) README quickstart (must ship with repo)

Install

Python venv; pip install -r requirements.txt

Ensure ffmpeg in PATH

Ensure ComfyUI is running at COMFY_HOST:COMFY_PORT

Set LLM creds in config.py (or env)

Run

python podcast_video_factory.py --audio input/episode.mp3


Outputs appear under output/{slug}/final.mp4

15) Security & safety

Never instruct the image model to draw text.

Filter/correct prompts that may lead to disallowed outputs.

Sanitise filenames; no path traversal.

Don’t log secrets.

Appendix A — Minimal Comfy graph (concept)

Coders must provide a JSON graph with:

CheckpointLoaderSimple(ckpt_name=...)

Positive/Negative CLIP text encoders (plug prompts)

Sampler with steps/cfg/sampler/scheduler/seed

VAE Decode → SaveImage (writes to COMFY_OUTPUT_DIR)

The comfy_client.build_graph() fills these params per segment.

Appendix B — Example LLM call (shape)

System: “You generate SD prompts for segment images. … [rules from §8.3]. Return strict JSON only.”
User: Provides:

GLOBAL_STYLE

Array of {segment_index, text, seconds}

Expected JSON: As in §7.2.

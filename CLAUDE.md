# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Podcast Video Factory (PCVF) is a CLI tool that converts long-form audio podcasts into engaging visual videos with AI-generated images and captions. The pipeline takes audio + optional transcript, segments it into fixed intervals, generates contextual image prompts via LLM, renders images through ComfyUI (Stable Diffusion), and assembles everything into an MP4 with burned-in captions using FFmpeg.

## Essential Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Or use the installer script
./install.sh

# Check GPU setup for faster transcription (optional)
python check_gpu_setup.py

# Setup GPU on WSL2 (optional, for 5-10x faster transcription)
./setup_gpu_wsl2.sh
```

### Running the Pipeline
```bash
# With audio only (will auto-transcribe using faster-whisper)
python podcast_video_factory.py --audio input/episode.mp3

# With pre-existing transcript (supports .srt, .json, .txt)
python podcast_video_factory.py --audio input/episode.mp3 --srt input/transcript.json

# Force regeneration (ignore cached segments/prompts/images)
python podcast_video_factory.py --audio input/episode.mp3 --force

# Control transcription device and model
python podcast_video_factory.py --audio input/episode.mp3 \
  --whisper-device auto --whisper-model base

# Force GPU transcription (requires CUDA + cuDNN)
python podcast_video_factory.py --audio input/episode.mp3 --whisper-device cuda

# Force CPU transcription (slower but compatible)
python podcast_video_factory.py --audio input/episode.mp3 --whisper-device cpu

# Override config parameters
python podcast_video_factory.py --audio input/episode.mp3 \
  --seg-sec 15 --width 1280 --height 720 --style "your custom style"
```

### Testing
```bash
# Run tests (pytest must be installed separately)
pytest tests/

# Run specific test files
pytest tests/test_units.py
pytest tests/test_acceptance.py
```

### Linting and Type Checking
```bash
# Install dev tools first
pip install ruff mypy pytest

# Check code style
ruff check .

# Format code
ruff format .

# Type checking
mypy .
```

## Architecture

### Pipeline Flow
1. **Transcription/Parsing** (`core/transcript_parser.py`) - Converts audio to timestamped text
2. **Segmentation** (`core/segmenter.py`) - Splits transcript into fixed-duration segments
3. **Prompt Generation** (`core/prompt_generator.py`) - LLM generates image prompts and captions per segment
4. **Image Generation** (`core/comfy_client.py`) - ComfyUI renders images from prompts
5. **Caption Creation** (`core/captions.py`) - Builds ASS subtitle file with hooks
6. **Video Assembly** (`core/video_assembler.py`) - FFmpeg stitches images + audio + captions → MP4

### Key Modules

**transcript_parser.py**: Multi-format parser supporting:
- `.srt` files via pysrt
- `.json` transcripts (Whisper-style with start/end/text fields)
- `.txt` speaker-tagged format `[SPEAKER_XX] - HH:MM:SS.MMM`
- Auto-transcription via faster-whisper when no transcript provided

**segmenter.py**: Fixed-interval segmentation (default 12s). Concatenates overlapping transcript text, truncates to MAX_SEG_TEXT_CHARS (900), merges short partials (<3s into previous segment).

**prompt_generator.py**: Calls OpenAI API (configurable endpoint/model) with structured JSON output. Incorporates GLOBAL_STYLE into prompts, ensures no text/watermarks in images, generates 6-12 word caption hooks. Includes retry logic with exponential backoff.

**comfy_client.py**: REST+WebSocket interface to ComfyUI. Builds workflow graphs from `workflows/comfy_template.json` template, replaces placeholder variables ($POSITIVE_PROMPT, $SEED, etc.), queues prompts, waits for image generation completion.

**captions.py**: Generates ASS subtitles using config font/color settings. Enforces CAPTION_MAX_CHARS, applies casing rules (title/sentence/none).

**video_assembler.py**: Creates FFmpeg concat list with image durations, overlays subtitles, outputs final MP4 with specified fps/bitrate.

### Configuration Philosophy

All runtime knobs live in `config.py` with CLI arg overrides. Key settings:
- `SEGMENT_SECONDS` (12) - Fixed segment duration
- `SEED` (123456) - Deterministic image generation (seed = SEED + segment_index)
- `ALLOW_REUSE` (True) - Cache segments/prompts/images unless `--force` flag
- `COMFY_HOST/COMFY_PORT` - ComfyUI server location
- `OPENAI_API_KEY` - LLM endpoint credentials (supports OpenAI-compatible APIs)

### Output Structure
```
output/{slug}/
├── segments.json       # Timestamped segments with text
├── prompts.json        # LLM-generated prompts and captions
├── images/            # Generated images (seg_000.png, seg_001.png, ...)
├── captions.ass       # ASS subtitle file
├── final.mp4          # Assembled video
└── run.log            # JSONL structured logs
```

## External Dependencies

**ComfyUI**: Must be running with SDXL checkpoint at configured host:port (default 127.0.0.1:8188). The pipeline uses `workflows/comfy_template.json` as a base graph template.

**FFmpeg**: Required in PATH for video assembly. Pipeline uses concat demuxer with explicit durations + subtitle filter.

**OpenAI API**: Set `OPENAI_API_KEY` environment variable or in config.py. Supports OpenAI-compatible endpoints via `OPENAI_BASE_URL`.

**GPU Acceleration (Optional)**: For 5-10x faster transcription, install CUDA Toolkit + cuDNN. Use `check_gpu_setup.py` to diagnose GPU status and `setup_gpu_wsl2.sh` to install on WSL2. Transcription defaults to `--whisper-device auto` which tries GPU and gracefully falls back to CPU.

## GPU Setup & Transcription

### Device Selection
- `--whisper-device auto` (default): Try GPU, fallback to CPU if unavailable
- `--whisper-device cuda`: Force GPU (requires CUDA + cuDNN)
- `--whisper-device cpu`: Force CPU (slower, more compatible)

### Model Selection
- `--whisper-model tiny`: Fastest, least accurate (~39M parameters)
- `--whisper-model base`: Fast, decent quality (~74M parameters)
- `--whisper-model small`: Balanced (~244M parameters)
- `--whisper-model medium`: High quality (~769M parameters)
- `--whisper-model large-v3`: Best quality, slowest (~1550M parameters, default)

### Speed Comparison
| Model | Device | Relative Speed |
|-------|--------|----------------|
| large-v3 | CUDA | 5-10x realtime |
| large-v3 | CPU | 0.5-1x realtime |
| base | CPU | 2-3x realtime |
| tiny | CPU | 5-8x realtime |

### GPU Setup Scripts
- `check_gpu_setup.py`: Diagnostic tool for NVIDIA drivers, CUDA, cuDNN, PyTorch, and faster-whisper
- `setup_gpu_wsl2.sh`: Automated installer for CUDA Toolkit + cuDNN on WSL2

## Development Notes

**Determinism**: Same inputs + seed produce identical outputs (segments, prompts, images). Critical for reproducibility.

**Graceful Degradation**: Pipeline includes skip logic when external dependencies unavailable (dummy prompts if no API key, placeholder images if ComfyUI down, dummy MP4 if FFmpeg missing). This allows partial testing without full stack.

**Retry Strategy**: LLM calls retry up to RETRY_LLM times with exponential backoff. ComfyUI operations retry up to RETRY_COMFY times.

**Transcript Formats**: When adding test data, ensure JSON transcripts have `start`/`end` (float seconds) + `text` fields. Text format requires `[SPEAKER_XX] - HH:MM:SS.MMM` pattern.

**Idempotency**: With `ALLOW_REUSE=True`, existing intermediate files are reused. Use `--force` to regenerate everything from scratch.

## Testing Strategy

**Unit Tests** (`tests/test_units.py`): Manual verification of parsing/segmenting logic with known inputs.

**Format-Specific Tests**: `test_parse_json.py` and `test_parse_text.py` validate individual parser functions.

**Acceptance Tests** (`tests/test_acceptance.py`): Integration test of parse → segment pipeline with real transcript data.

**Full Pipeline Testing**: Run with test data in `input/` directory. Validate:
- Image count == segment count
- Video duration matches audio ±1s
- Captions render correctly in final MP4
- All JSON schemas match spec in INSTRUCTIONS.md

## Code Conventions

- Snake_case for functions/variables
- Type hints on all function signatures
- Modular `/core/` structure for reusable components
- Config-driven design (avoid hardcoded values)
- Error handling with retries for external services
- JSONL structured logging via `logging_utils.py`

## Security Considerations

- Never instruct SD to render text/typography in images (enforced in LLM system prompt)
- Sanitize filenames to prevent path traversal
- Don't log API keys or secrets
- Filter prompts that may violate content policies

## Known Limitations (v1)

- Fixed-length segments only (semantic boundaries planned for Phase 2)
- Still images only (no animation/video diffusion)
- Sequential image generation (no parallelization)
- Hard cuts between scenes (no transitions)
- Single-pass FFmpeg assembly (no multi-stream optimization)

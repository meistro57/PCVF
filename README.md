# Podcast Video Factory

Description: Turns long-form audio podcasts into engaging visual videos with AI-generated images and captions.

## Quickstart

1. Install dependencies: `pip install -r requirements.txt`
2. Ensure FFmpeg is installed and in PATH.
3. Start ComfyUI with SDXL checkpoint on port 8188.
4. Set OPENAI_API_KEY in env or config.py.
5. Run: `python podcast_video_factory.py --audio input/episode.mp3`

Outputs: output/{slug}/final.mp4 with logs, segments, prompts, images.

## Pipeline Overview

1. Transcription/Parsing (SRT or Whisper)
2. Segmentation into fixed intervals
3. Prompt Generation (LLM)
4. Image Generation (ComfyUI)
5. Caption creation (ASS subtitles)
6. Video Assembly (FFmpeg)

## Development

```bash
pip install -r requirements.txt
pip install ruff mypy pytest
pytest
ruff check .
mypy .
```
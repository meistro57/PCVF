<div align="center">

# 🎙️ Podcast Video Factory

### Transform Audio into Visual Stories

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-orange.svg)](version.py)

*Turn long-form audio podcasts into engaging visual videos with AI-generated images, dynamic captions, and cinematic style.*

[Features](#-features) • [Quick Start](#-quick-start) • [Usage](#-usage) • [GPU Setup](#-gpu-acceleration) • [Pipeline](#-pipeline-overview)

</div>

---

## ✨ Features

- 🎤 **Automatic Transcription** - Uses Whisper AI for accurate speech-to-text
- 🖼️ **AI Image Generation** - Creates contextual visuals via Stable Diffusion (ComfyUI)
- 💬 **Dynamic Captions** - Burned-in subtitles with hooks and visual styling
- ⚡ **GPU Acceleration** - Optional CUDA support for 5-10x faster transcription
- 🔄 **Intelligent Caching** - Reuses intermediate files to save time and costs
- 🎨 **Customizable Style** - Control visual aesthetics via global style prompts
- 📊 **Multiple Formats** - Supports SRT, JSON, TXT transcript inputs
- 🎯 **Deterministic Output** - Same inputs always produce identical results

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/PCVF.git
cd PCVF

# Install dependencies
pip install -r requirements.txt

# Or use the automated installer
./install.sh
```

### Prerequisites

- **Python 3.8+**
- **FFmpeg** (for video assembly)
- **ComfyUI** with SDXL checkpoint (for image generation)
- **OpenAI API Key** (for prompt generation)

### Basic Usage

```bash
# Simple: Just provide audio
python podcast_video_factory.py --audio input/episode.mp3

# With custom settings
python podcast_video_factory.py \
  --audio input/episode.mp3 \
  --whisper-model base \
  --style "cyberpunk, neon, futuristic"
```

**Output:** `output/{episode-name}/final.mp4` 🎬

## 📖 Usage

### Command-Line Options

```bash
# Audio & Transcription
--audio PATH              Input audio file (required)
--srt PATH               Pre-existing transcript (.srt/.json/.txt)
--whisper-model SIZE     Model size: tiny|base|small|medium|large-v3
--whisper-device DEVICE  Device: auto|cuda|cpu

# Visual Settings
--width INT              Video width (default: 1920)
--height INT             Video height (default: 1080)
--fps INT                Frame rate (default: 30)
--style TEXT             Global visual style prompt

# Pipeline Control
--seg-sec INT            Segment duration in seconds (default: 12)
--force                  Regenerate all cached files
--out PATH               Output directory (default: ./output)

# Info
--version                Show version and exit
--help                   Show help message
```

### Examples

```bash
# Fast transcription with smaller model
python podcast_video_factory.py --audio input/talk.mp3 --whisper-model base

# Custom visual style
python podcast_video_factory.py \
  --audio input/podcast.m4a \
  --style "minimalist, pastel colors, soft lighting"

# Force GPU transcription (requires CUDA)
python podcast_video_factory.py --audio input/ep1.mp3 --whisper-device cuda

# Use pre-existing transcript
python podcast_video_factory.py \
  --audio input/interview.mp3 \
  --srt input/transcript.json
```

## ⚡ GPU Acceleration

Speed up transcription by **5-10x** with GPU support!

### Check GPU Status

```bash
python check_gpu_setup.py
```

### Setup GPU (WSL2)

```bash
./setup_gpu_wsl2.sh
```

### Performance Comparison

| Model | Device | Speed | Accuracy |
|-------|--------|-------|----------|
| large-v3 | GPU | 🚀🚀🚀🚀🚀 5-10x realtime | ⭐⭐⭐⭐⭐ Best |
| large-v3 | CPU | 🐌 0.5-1x realtime | ⭐⭐⭐⭐⭐ Best |
| base | CPU | 🚀🚀 2-3x realtime | ⭐⭐⭐ Good |
| tiny | CPU | 🚀🚀🚀🚀 5-8x realtime | ⭐⭐ Fair |

## 🔄 Pipeline Overview

```
┌─────────────┐
│ Audio Input │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Transcription  │ ← faster-whisper
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│  Segmentation    │ ← Fixed intervals (12s)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Prompt Generation│ ← OpenAI GPT
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Image Generation │ ← ComfyUI + SDXL
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Caption Creation │ ← ASS subtitles
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Video Assembly   │ ← FFmpeg
└────────┬─────────┘
         │
         ▼
    📹 final.mp4
```

### Output Structure

```
output/{episode-slug}/
├── segments.json       # Timestamped transcript segments
├── prompts.json        # AI-generated image prompts & captions
├── images/             # Generated images (seg_000.png, seg_001.png, ...)
├── captions.ass        # Subtitle file with styling
├── final.mp4          # 🎬 Final video output
└── run.log            # Detailed execution logs
```

## 🛠️ Development

### Setup Dev Environment

```bash
pip install -r requirements.txt
pip install ruff mypy pytest
```

### Run Tests

```bash
pytest tests/              # All tests
pytest tests/test_units.py # Unit tests only
```

### Code Quality

```bash
ruff check .    # Linting
ruff format .   # Formatting
mypy .          # Type checking
```

## 📋 Configuration

Edit `config.py` to customize defaults:

```python
# Segmentation
SEGMENT_SECONDS = 12
MAX_SEG_TEXT_CHARS = 900

# Visual Style
GLOBAL_STYLE = "cinematic, sacred geometry, cosmic-tech elegance"
WIDTH = 1920
HEIGHT = 1080

# LLM
OPENAI_MODEL = "gpt-4o-mini"

# ComfyUI
COMFY_HOST = "127.0.0.1"
COMFY_PORT = 8188
```

## 🤝 Contributing

Contributions welcome! Please read [CLAUDE.md](CLAUDE.md) for development guidelines.

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation:** [CLAUDE.md](CLAUDE.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Issues:** [GitHub Issues](https://github.com/yourusername/PCVF/issues)

---

<div align="center">

**Built with ❤️ using Whisper, GPT, Stable Diffusion, and FFmpeg**

</div>
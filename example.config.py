# Podcast Video Factory Configuration
# Copy this file to config.py and customize for your setup

import os

# IO
AUDIO_PATH = "input/episode.mp3"
SRT_PATH = None  # If None, transcribe
OUTPUT_ROOT = "output"

# Segmentation
SEGMENT_SECONDS = 12
MAX_SEG_TEXT_CHARS = 900

# Captions (ASS)
CAPTION_MAX_CHARS = 88
CAPTION_CASE = "title"  # "title" | "sentence" | "none"
CAPTION_FONT = "DejaVu Sans"
CAPTION_FONTSIZE = 42
CAPTION_MARGIN = 60
CAPTION_STROKE = 2
CAPTION_BG_ALPHA = 0.35

# LLM (OpenAI-compatible API)
# Set OPENAI_API_KEY environment variable or replace "YOUR_KEY" below
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = "gpt-4o-mini"

# Global visual style
GLOBAL_STYLE = "cinematic, sacred geometry, cosmic-tech elegance, crisp detail, clean composition, dramatic lighting, high dynamic range"
NEGATIVE_STYLE = "blurry, watermark, text, logo, extra limbs, distorted, low-res"

# Image generation / ComfyUI
WIDTH = 1920
HEIGHT = 1080
SEED = 123456
STEPS = 30
CFG = 6.5
SAMPLER_NAME = "euler"
SCHEDULER = "normal"
BATCH_SIZE = 1
COMFY_HOST = "127.0.0.1"
COMFY_PORT = 8188
COMFY_OUTPUT_DIR = "output"

# FFmpeg
FFMPEG_EXE = "ffmpeg"
VIDEO_FPS = 30
VIDEO_BITRATE = "10M"

# Behaviour
ALLOW_REUSE = True
RETRY_LLM = 3
RETRY_COMFY = 2
TIMEOUT_COMFY_SEC = 600

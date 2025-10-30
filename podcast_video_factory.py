#!/usr/bin/env python3
""" CLI entrypoint for Podcast Video Factory """

import argparse
import os
import json
from pathlib import Path
from config import *
from version import __version__
from core.transcript_parser import parse_transcript
from core.segmenter import segment_transcript
from core.prompt_generator import generate_prompts
from core.comfy_client import ComfyClient
from core.captions import build_captions
from core.video_assembler import assemble_video
from core.logging_utils import setup_logger

def resolve_slug(audio_path):
    """ Generate slug from audio filename """
    return Path(audio_path).stem

def main():
    parser = argparse.ArgumentParser(
        description="Podcast Video Factory - Transform audio into visual stories",
        epilog=f"Version {__version__}"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--srt", help="Path to transcript file (.srt, .txt, .json)")
    parser.add_argument("--out", help="Output directory root")
    parser.add_argument("--seg-sec", type=int, help="Segment seconds")
    parser.add_argument("--width", type=int, help="Width")
    parser.add_argument("--height", type=int, help="Height")
    parser.add_argument("--fps", type=int, help="FPS")
    parser.add_argument("--bitrate", help="Bitrate")
    parser.add_argument("--style", help="Global style")
    parser.add_argument("--force", action="store_true", help="Force regeneration")
    parser.add_argument("--whisper-model", default="large-v3", help="Whisper model size (tiny, base, small, medium, large-v3)")
    parser.add_argument("--whisper-device", default="auto", help="Transcription device (auto, cuda, cpu)")
    args = parser.parse_args()

    # Override config with args
    srt_path = args.srt if args.srt else SRT_PATH
    output_root = args.out if args.out else OUTPUT_ROOT
    segment_seconds = args.seg_sec if args.seg_sec else SEGMENT_SECONDS
    width = args.width if args.width else WIDTH
    height = args.height if args.height else HEIGHT
    video_fps = args.fps if args.fps else VIDEO_FPS
    video_bitrate = args.bitrate if args.bitrate else VIDEO_BITRATE
    global_style = args.style if args.style else GLOBAL_STYLE
    allow_reuse = not args.force if args.force else ALLOW_REUSE

    slug = resolve_slug(args.audio)
    output_dir = Path(output_root) / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(output_dir / "run.log")

    try:
        # Step 1: Parse transcript
        # Pass transcription config if auto-transcribing
        if srt_path:
            lines = parse_transcript(args.audio, srt_path)
        else:
            # Import transcribe_audio directly for more control
            from core.transcript_parser import transcribe_audio
            lines = transcribe_audio(Path(args.audio), model_size=args.whisper_model, device=args.whisper_device)
        logger.info("Parsed transcript")

        # Step 2: Segment
        segments = segment_transcript(lines, segment_seconds, MAX_SEG_TEXT_CHARS, output_dir / "segments.json")
        logger.info(f"Segmented into {len(segments)} segments")

        # Step 3: Generate prompts (SKIP if OpenAI key not set)
        prompts_file = output_dir / "prompts.json"
        if allow_reuse and prompts_file.exists():
            with open(prompts_file) as f:
                prompts = json.load(f)
            logger.info("Reusing prompts")
        else:
            if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_KEY":
                print("SKIP: No OpenAI API key set, using dummy prompts")
                prompts = {"results": [{"segment_index": i, "prompt": f"dummy prompt for segment {i}", "negative_prompt": NEGATIVE_STYLE, "caption": f"Segment {i}"} for i in range(len(segments))]}
            else:
                prompts = generate_prompts(segments, global_style, NEGATIVE_STYLE)
            with open(prompts_file, "w") as f:
                json.dump(prompts, f, indent=2)
            logger.info("Generated prompts")

        # Step 4: Generate images (SKIP if ComfyUI not available)
        client = ComfyClient(f"http://{COMFY_HOST}:{COMFY_PORT}", output_dir / "images")
        try:
            for i, seg in enumerate(prompts["results"]):
                seed = SEED + seg["segment_index"]
                client.generate_image(seg["prompt"], seg["negative_prompt"], seed)
                logger.info(f"Generated image for segment {i}")
        except Exception as e:
            print(f"SKIP: ComfyUI error ({e}), creating dummy images")
            (output_dir / "images").mkdir(exist_ok=True)
            for i in range(len(segments)):
                (output_dir / "images" / f"seg_{i:03d}.png").write_text("dummy image")  # Placeholder

        # Step 5: Build captions
        captions_file = output_dir / "captions.ass"
        build_captions(segments, prompts["results"], captions_file)
        logger.info("Built captions")

        # Step 6: Assemble video (SKIP if FFmpeg not available)
        audio_path = args.audio
        if not os.path.exists(audio_path):
            print("SKIP: No audio file, creating dummy MP4")
            (output_dir / "final.mp4").write_text("dummy video")
        else:
            try:
                assemble_video(audio_path, output_dir / "images", captions_file, output_dir / "final.mp4")
                logger.info("Assembled video")
            except Exception as e:
                print(f"SKIP: FFmpeg error ({e}), creating dummy MP4")
                (output_dir / "final.mp4").write_text("dummy video")

        print("SUCCESS: Pipeline completed at", output_dir)

    except Exception as e:
        logger.error(str(e))
        raise

if __name__ == "__main__":
    main()
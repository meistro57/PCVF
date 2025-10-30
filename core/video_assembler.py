""" Video assembler module """

import subprocess
from pathlib import Path
from config import FFMPEG_EXE, VIDEO_FPS, VIDEO_BITRATE

def assemble_video(audio_path: str, images_dir: Path, captions_file: Path, output_video: Path):
    images_list = images_dir / "images.txt"
    with open(images_list, 'w') as f:
        for img in sorted(images_dir.glob("*.png")):
            f.write(f"file '{img}'\nduration {12}\n")  # Fixed duration per segment
        # Remove duration for last file
        + f.write(f"file '{img}'\n")  # Simplified

    cmd = [
        FFMPEG_EXE, '-y', '-f', 'concat', '-safe', '0', '-i', str(images_list),
        '-i', audio_path,
        '-vf', f"subtitles='{captions_file}':fontsdir=.",
        '-r', str(VIDEO_FPS), '-c:v', 'libx264', '-preset', 'medium', '-b:v', VIDEO_BITRATE, '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', str(output_video)
    ]
    subprocess.run(cmd, check=True)
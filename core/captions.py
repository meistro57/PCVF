""" Captions module """

from pathlib import Path
from config import CAPTION_FONT, CAPTION_FONTSIZE, CAPTION_MARGIN, CAPTION_STROKE, CAPTION_BG_ALPHA, CAPTION_CASE, CAPTION_MAX_CHARS
from typing import List, NamedTuple, Dict
from core.segmenter import Segment, Segment

class PromptResult(NamedTuple):
    segment_index: int
    prompt: str
    negative_prompt: str
    caption: str

def build_captions(segments: List[Segment], results: List[Dict], output_file: Path):
    ass_script = """
[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{fontname},{fontsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&H{COLOR},-1,0,0,0,100,100,0,0,1,{stroke},0,5,0,0,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(fontname=CAPTION_FONT, fontsize=CAPTION_FONTSIZE, stroke=CAPTION_STROKE, margin=CAPTION_MARGIN, COLOR=f"{int(CAPTION_BG_ALPHA*255):02X}000000")

    for i, seg in enumerate(segments):
        start_time = format_ms(seg.start_ms)
        end_time = format_ms(seg.end_ms)
        caption = results[i]['caption'][:CAPTION_MAX_CHARS]
        if CAPTION_CASE == 'title':
            caption = caption.title()
        ass_script += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{caption}\n"

    with open(output_file, 'w') as f:
        f.write(ass_script)

def format_ms(ms):
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{seconds:02}.{ms:02}"
""" Transcript parser module """

import json
import re
from pathlib import Path
from typing import List, NamedTuple
from faster_whisper import WhisperModel
import pysrt

class Line(NamedTuple):
    start_ms: int
    end_ms: int
    text: str

def parse_srt(srt_path: Path) -> List[Line]:
    """ Parse SRT file into Lines """
    subs = pysrt.open(srt_path)
    lines = []
    for sub in subs:
        text = sub.text.strip().replace('\n', ' ')
        lines.append(Line(sub.start.ordinal, sub.end.ordinal, text))
    return lines

def parse_json_transcript(json_path: Path) -> List[Line]:
    """ Parse JSON transcript (e.g., from OpenAI Whisper) """
    with open(json_path) as f:
        data = json.load(f)
    lines = []
    for item in data:
        start_ms = int(item['start'] * 1000)
        end_ms = int(item['end'] * 1000)
        text = item['text'].strip()
        lines.append(Line(start_ms, end_ms, text))
    return lines

def parse_text_transcript(text_path: Path) -> List[Line]:
    """ Parse text transcript with [SPEAKER_XX] - HH:MM:SS.MMM format """
    lines = []
    with open(text_path) as f:
        content = f.read()
    
    # Regex to find entries like [SPEAKER_01] - 00:00:00.000
    pattern = re.compile(r'\[([^\]]+)\]\s*-\s*(\d{1,2}):(\d{2}):(\d{2})\.(\d{3})\s*(.*?)(?=\n\[|\n$|$)', re.DOTALL)
    
    for match in pattern.findall(content):
        speaker, hh, mm, ss, mmm, text_chunk = match
        hh, mm, ss, mmm = map(int, [hh, mm, ss, mmm])
        start_ms = (hh * 3600 + mm * 60 + ss) * 1000 + mmm
        
        # Simple heuristic: split text into lines, estimate duration
        text_lines = [line.strip() for line in text_chunk.split('\n') if line.strip()]
        duration_per_line = 3000  # 3 seconds per line estimate
        for i, t in enumerate(text_lines):
            lines.append(Line(start_ms + i*duration_per_line, start_ms + (i+1)*duration_per_line, t))
    
    return lines

def transcribe_audio(audio_path: Path, model_size="large-v3") -> List[Line]:
    """ Transcribe audio using faster-whisper (not used in testing) """
    model = WhisperModel(model_size)
    segments, info = model.transcribe(str(audio_path))
    srt_path = audio_path.with_suffix('.srt')
    with open(srt_path, 'w') as f:
        for i, segment in enumerate(segments):
            f.write(f"{i+1}\n")
            f.write(f"{format_time(segment.start)} --> {format_time(segment.end)}\n")
            f.write(f"{segment.text}\n\n")
    return parse_srt(srt_path)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}".replace('.', ',')

def parse_transcript(audio_path: str, srt_path: str = None) -> List[Line]:
    """ Main parse function """
    if srt_path:
        path = Path(srt_path)
        if path.suffix == '.json':
            return parse_json_transcript(path)
        elif path.suffix == '.txt':
            return parse_text_transcript(path)
        elif path.suffix == '.srt':
            return parse_srt(path)
        else:
            raise ValueError("Unsupported transcript format")
    else:
        return transcribe_audio(Path(audio_path))
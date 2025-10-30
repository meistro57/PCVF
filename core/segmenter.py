""" Segmenter module """

import json
from config import MAX_SEG_TEXT_CHARS
from core.transcript_parser import Line
from typing import List, NamedTuple
from pathlib import Path

class Segment(NamedTuple):
    index: int
    start_ms: int
    end_ms: int
    text: str

def segment_transcript(lines: List[Line], segment_seconds: int, max_chars: int, output_file: Path = None) -> List[Segment]:
    total_duration = lines[-1].end_ms if lines else 0
    segment_ms = segment_seconds * 1000
    segments = []

    for i in range(0, total_duration, segment_ms):
        start_ms = i
        end_ms = min(i + segment_ms, total_duration)
        if end_ms - start_ms < 3000 and i > 0:  # Merge if <3s and not first
            # Replace last segment with extended version (NamedTuple is immutable)
            prev = segments[-1]
            segments[-1] = Segment(index=prev.index, start_ms=prev.start_ms, end_ms=end_ms, text=prev.text)
            continue

        text_parts = []
        for line in lines:
            if line.start_ms < end_ms and line.end_ms > start_ms:
                overlap_start = max(start_ms, line.start_ms)
                overlap_end = min(end_ms, line.end_ms)
                if overlap_end > overlap_start:
                    text_parts.append(line.text)

        full_text = ' '.join(text_parts)[:max_chars]
        segments.append(Segment(index=i//segment_ms, start_ms=start_ms, end_ms=end_ms, text=full_text))

    if output_file:
        data = [{"index": s.index, "start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text} for s in segments]
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

    return segments
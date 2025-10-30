#!/usr/bin/env python3
""" Basic acceptance test: parse transcript, segment, and verify """

import os
from pathlib import Path
from core.transcript_parser import parse_transcript
from core.segmenter import segment_transcript

def test_basic_parse_and_segment():
    """ Test parsing transcript and segmenting without full pipeline """
    # Use the provided JSON transcript
    transcript_path = "Time_Traveler_Pensions,_Quantum_Minds,_and_the_ADHD_Spiritual/transcript.json"
    
    if not Path(transcript_path).exists():
        print("Transcript file not found, skipping")
        return
    
    lines = parse_transcript(audio_path=None, srt_path=transcript_path)
    print(f"Parsed {len(lines)} lines from JSON transcript")
    
    # Segment
    segments = segment_transcript(lines, segment_seconds=12, max_chars=900)
    print(f"Segmented into {len(segments)} segments")
    
    # Verify
    assert len(segments) > 0
    assert all(s.end_ms - s.start_ms > 0 for s in segments)
    assert all(len(s.text) <= 900 for s in segments)
    
    print("Acceptance test passed!")

if __name__ == "__main__":
    test_basic_parse_and_segment()
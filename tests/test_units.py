#!/usr/bin/env python3
""" Unit tests for core modules """

import pytest
from core.transcript_parser import parse_transcript, Line
from core.segmenter import segment_transcript
from pathlib import Path
import tempfile

def test_parse_srt():
    with tempfile.NamedTemporaryFile(suffix=".srt", mode="w", delete=False) as f:
        f.write("1\n00:00:00,000 --> 00:00:05,000\nHello\n\n2\n00:00:05,000 --> 00:00:10,000\nWorld\n")
        f.flush()
        lines = parse_transcript(None, f.name)
    Path(f.name).unlink()
    assert len(lines) == 2
    assert lines[0].text == "Hello"
    assert lines[1].text == "World"

def test_segment_transcript():
    lines = [
        Line(0, 2000, "Test 1"),
        Line(2000, 4000, "Test 2"),
        Line(4000, 6000, "Test 3")
    ]
    segments = segment_transcript(lines, 3, 900)
    assert len(segments) == 2
    assert segments[0].start_ms == 0
    assert segments[1].start_ms == 3000

def test_prompt_generator_no_api():
    # Skip without key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No API key")

def test_video_assembler_no_files():
    # Would require FFmpeg and files
    pass

# Run with pytest if needed
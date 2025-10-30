# Podcast Video Factory - Improvement Suggestions

## Critical Bugs 🔴

### 1. **video_assembler.py:11-13 - Incorrect FFmpeg concat list generation**
**Issue**: Hardcoded duration (12s) and syntax error in file writing
```python
# Current (BROKEN):
for img in sorted(images_dir.glob("*.png")):
    f.write(f"file '{img}'\nduration {12}\n")
    # Remove duration for last file
    + f.write(f"file '{img}'\n")  # ← Invalid syntax + wrong logic
```

**Fix**: Use SEGMENT_SECONDS from config and handle last image correctly
```python
images = sorted(images_dir.glob("*.png"))
for i, img in enumerate(images[:-1]):
    f.write(f"file '{img.name}'\nduration {SEGMENT_SECONDS}\n")
# Last image needs no duration (or use audio length)
if images:
    f.write(f"file '{images[-1].name}'\n")
```

### 2. **podcast_video_factory.py:48 - mkdir syntax error**
**Issue**: Invalid parameter name
```python
output_dir.mkdir(parents_ok=True)  # ← Wrong parameter name
```
**Fix**:
```python
output_dir.mkdir(parents=True, exist_ok=True)
```

### 3. **podcast_video_factory.py:36-44 - Config variable scope issue**
**Issue**: Local assignments don't affect imported config values in modules
```python
if args.srt: SRT_PATH = args.srt  # ← Doesn't affect config.SRT_PATH
```
**Fix**: Pass config overrides as parameters or use a Config object
```python
# Option 1: Config class
from dataclasses import dataclass
@dataclass
class Config:
    segment_seconds: int = 12
    # ... other fields

config = Config()
if args.seg_sec: config.segment_seconds = args.seg_sec
```

### 4. **comfy_client.py:55 - Undefined variable reference**
**Issue**: `segment_index` is referenced but not passed to `build_graph()`
```python
value = value.replace('$INDEX', str(segment_index))  # ← undefined
```
**Fix**: Add segment_index parameter
```python
def generate_image(self, positive, negative, seed, segment_index, ...):
    graph = self.build_graph(positive, negative, ..., segment_index)
```

### 5. **captions.py:6 - Duplicate import**
**Issue**: Imports Segment twice
```python
from core.segmenter import Segment, Segment  # ← duplicate
```
**Fix**: Remove duplicate

### 6. **comfy_template.json:12 - Invalid ComfyUI graph structure**
**Issue**: Node "2" references `["1", 1]` (CLIP output from text encoder) but node "1" is CLIPTextEncode which only has one output
```json
"2": {
  "inputs": {
    "clip": ["1", 1]  // ← Should be ["3", 1] (from CheckpointLoader)
  }
}
```
**Fix**: Reference checkpoint loader's CLIP output
```json
"1": {
  "class_type": "CLIPTextEncode",
  "inputs": {
    "text": "$POSITIVE_PROMPT",
    "clip": ["3", 1]  // ← Get CLIP from checkpoint
  }
}
```

### 7. **segmenter.py:24 - Segment merge doesn't work**
**Issue**: Tries to modify immutable NamedTuple
```python
if end_ms - start_ms < 3000 and i > 0:
    segments[-1].end_ms = end_ms  # ← NamedTuple is immutable!
    continue
```
**Fix**: Use regular class or recreate tuple
```python
if end_ms - start_ms < 3000 and i > 0:
    prev = segments.pop()
    segments.append(Segment(prev.index, prev.start_ms, end_ms, prev.text))
    continue
```

### 8. **captions.py:44 - Incorrect millisecond formatting**
**Issue**: ASS format expects centiseconds (1/100th), not milliseconds truncated to 2 digits
```python
return f"{hours}:{minutes:02}:{seconds:02}.{ms:02}"  # ← Wrong: 500ms → .50 (should be .50 centiseconds)
```
**Fix**:
```python
centiseconds = ms // 10
return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"
```

## Architecture & Design Issues 🏗️

### 9. **No actual JSONL logging**
**Issue**: logging_utils.py uses standard format, not JSONL as required by spec
**Fix**: Implement proper JSONL formatter
```python
class JSONLFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_data)
```

### 10. **ComfyClient WebSocket implementation is a stub**
**Issue**: `wait_for_completion()` just sleeps 5 seconds instead of actually monitoring
**Fix**: Implement proper WebSocket handling
```python
import websocket
def wait_for_completion(self, prompt_id, client_id):
    ws = websocket.create_connection(f"{self.ws_url}/ws?clientId={client_id}")
    while True:
        msg = json.loads(ws.recv())
        if msg.get("type") == "execution_error":
            raise Exception(f"ComfyUI error: {msg}")
        if msg.get("type") == "executed" and msg.get("data", {}).get("prompt_id") == prompt_id:
            return msg["data"]["output"]
    ws.close()
```

### 11. **No manifest.json generation**
**Issue**: Spec requires manifest.json with metadata about images/seeds/outputs
**Fix**: Add to podcast_video_factory.py after assembly
```python
manifest = {
    "audio": args.audio,
    "slug": slug,
    "output": str(output_dir / "final.mp4"),
    "segments": "segments.json",
    "prompts": "prompts.json",
    "images": [
        {"segment_index": i, "file": f"images/seg_{i:03d}.png", "seed": SEED + i}
        for i in range(len(segments))
    ],
    "video": {"fps": VIDEO_FPS, "bitrate": VIDEO_BITRATE, "size": f"{WIDTH}x{HEIGHT}"}
}
with open(output_dir / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
```

### 12. **Missing dependency validation**
**Issue**: No checks for FFmpeg, ComfyUI, or API keys at startup
**Fix**: Add validation function
```python
def validate_dependencies():
    # Check FFmpeg
    if shutil.which(FFMPEG_EXE) is None:
        raise RuntimeError(f"{FFMPEG_EXE} not found in PATH")

    # Check ComfyUI
    try:
        r = requests.get(f"http://{COMFY_HOST}:{COMFY_PORT}/system_stats", timeout=5)
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"ComfyUI not reachable at {COMFY_HOST}:{COMFY_PORT}: {e}")

    # Check API key
    if OPENAI_API_KEY == "YOUR_KEY":
        raise RuntimeError("OPENAI_API_KEY not set")
```

### 13. **Reloading comfy_template.json for every image**
**Issue**: File is read from disk for each segment
**Fix**: Load once and reuse
```python
class ComfyClient:
    def __init__(self, comfy_url, output_dir):
        self.url = comfy_url
        self.output_dir = output_dir
        # Load template once
        with open('workflows/comfy_template.json') as f:
            self.template = json.load(f)
```

### 14. **Error handling inconsistency**
**Issue**: Mix of try/except, skip logic with print(), and unhandled errors
**Fix**: Standardize error handling with custom exceptions
```python
class PipelineError(Exception):
    """Base exception for pipeline errors"""
    pass

class DependencyError(PipelineError):
    """External dependency unavailable"""
    pass

class ValidationError(PipelineError):
    """Input validation failed"""
    pass

# Usage
try:
    validate_dependencies()
    # ... pipeline steps
except DependencyError as e:
    logger.error(f"Dependency error: {e}")
    sys.exit(1)
```

## Code Quality Issues 📝

### 15. **Missing type hints in several places**
**Issue**: Some functions lack proper type annotations
**Fix**: Add complete type hints
```python
from typing import List, Dict, Any, Optional

def generate_prompts(
    segments: List[Segment],
    global_style: str,
    negative_style: str,
    retry: int = RETRY_LLM
) -> Dict[str, Any]:
    ...
```

### 16. **No LLM response validation**
**Issue**: JSON from LLM is not validated against expected schema
**Fix**: Add validation with jsonschema or pydantic
```python
from jsonschema import validate, ValidationError

PROMPT_SCHEMA = {
    "type": "object",
    "required": ["results"],
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["segment_index", "prompt", "negative_prompt", "caption"],
                "properties": {
                    "segment_index": {"type": "integer"},
                    "prompt": {"type": "string"},
                    "negative_prompt": {"type": "string"},
                    "caption": {"type": "string", "maxLength": 12}
                }
            }
        }
    }
}

result = json.loads(response.choices[0].message.content)
validate(result, PROMPT_SCHEMA)  # Raises ValidationError if invalid
return result
```

### 17. **Magic numbers throughout code**
**Issue**: Hardcoded values like 3000ms, 900 chars, 5s timeout
**Fix**: Move to config or constants
```python
# In config.py
MIN_SEGMENT_MS = 3000  # Merge segments shorter than this
WEBSOCKET_POLL_INTERVAL = 1.0  # seconds
TRANSCRIPTION_MODEL = "large-v3"
```

### 18. **No input sanitization**
**Issue**: Filenames from user input not sanitized
**Fix**: Add sanitization
```python
import re

def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filename"""
    # Remove path separators and dangerous chars
    safe = re.sub(r'[^\w\s-]', '', filename)
    safe = re.sub(r'[-\s]+', '_', safe)
    return safe[:255]  # Limit length

slug = sanitize_filename(Path(args.audio).stem)
```

### 19. **subprocess doesn't capture stderr**
**Issue**: FFmpeg errors not captured for debugging
**Fix**: Capture and log stderr
```python
result = subprocess.run(cmd, capture_output=True, text=True, check=False)
if result.returncode != 0:
    logger.error(f"FFmpeg failed: {result.stderr}")
    raise RuntimeError(f"Video assembly failed: {result.stderr}")
```

### 20. **No progress indicators**
**Issue**: Long operations provide no user feedback
**Fix**: Add tqdm progress bars
```python
from tqdm import tqdm

# In prompt generation
for i, seg in enumerate(tqdm(segments, desc="Generating prompts")):
    ...

# In image generation
for i, seg in enumerate(tqdm(prompts["results"], desc="Generating images")):
    ...
```

## Testing Issues 🧪

### 21. **Minimal test coverage**
**Issue**: Tests are sparse and incomplete
**Fix**: Add comprehensive test suite
```python
# tests/test_integration.py
def test_full_pipeline_with_mocks(tmp_path):
    """Test complete pipeline with mocked external dependencies"""
    # Mock OpenAI
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = ...

        # Mock ComfyUI
        with patch('requests.post') as mock_post:
            # Run pipeline
            result = main(["--audio", "test.mp3", "--out", str(tmp_path)])

            # Verify outputs
            assert (tmp_path / "segments.json").exists()
            assert (tmp_path / "prompts.json").exists()
            assert (tmp_path / "final.mp4").exists()
```

### 22. **No fixture management**
**Issue**: Tests create temp files manually
**Fix**: Use pytest fixtures
```python
@pytest.fixture
def sample_srt(tmp_path):
    srt_file = tmp_path / "test.srt"
    srt_file.write_text("""1
00:00:00,000 --> 00:00:05,000
Test content
""")
    return srt_file

def test_parse_srt(sample_srt):
    lines = parse_transcript(None, str(sample_srt))
    assert len(lines) == 1
```

### 23. **Hardcoded test paths**
**Issue**: Tests use relative paths that fail outside project root
**Fix**: Use proper path resolution
```python
TEST_DATA_DIR = Path(__file__).parent / "test_data"
transcript_path = TEST_DATA_DIR / "transcript.json"
```

### 24. **No CI/CD configuration**
**Issue**: No automated testing
**Fix**: Add GitHub Actions workflow
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest --cov=core --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Performance Issues ⚡

### 25. **Sequential image generation**
**Issue**: Images generated one-by-one even when ComfyUI could handle batches
**Fix**: Implement parallel generation with queue
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_images_parallel(client, prompts, max_workers=3):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                client.generate_image,
                p["prompt"],
                p["negative_prompt"],
                SEED + p["segment_index"],
                p["segment_index"]
            ): p["segment_index"]
            for p in prompts["results"]
        }

        for future in tqdm(as_completed(futures), total=len(futures)):
            segment_idx = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Segment {segment_idx} failed: {e}")
```

### 26. **No Whisper model caching**
**Issue**: WhisperModel loaded each time, slow for repeated runs
**Fix**: Cache model instance
```python
_whisper_cache = {}

def get_whisper_model(model_size="large-v3"):
    if model_size not in _whisper_cache:
        _whisper_cache[model_size] = WhisperModel(model_size)
    return _whisper_cache[model_size]
```

### 27. **No connection pooling**
**Issue**: ComfyClient creates new connections for each request
**Fix**: Use requests.Session
```python
class ComfyClient:
    def __init__(self, comfy_url, output_dir):
        self.url = comfy_url
        self.output_dir = output_dir
        self.session = requests.Session()

    def queue_prompt(self, prompt):
        response = self.session.post(f"{self.url}/prompt", json=prompt)
        return response.json()['prompt_id']
```

## Security & Safety Issues 🔒

### 28. **API keys in error messages**
**Issue**: Exceptions might leak OPENAI_API_KEY
**Fix**: Sanitize error messages
```python
def sanitize_error(error_str: str) -> str:
    """Remove sensitive data from error messages"""
    if OPENAI_API_KEY and OPENAI_API_KEY in error_str:
        error_str = error_str.replace(OPENAI_API_KEY, "***REDACTED***")
    return error_str
```

### 29. **No config validation**
**Issue**: Invalid config values (negative numbers, bad URLs) not caught
**Fix**: Add validation
```python
def validate_config():
    """Validate configuration values"""
    assert SEGMENT_SECONDS > 0, "SEGMENT_SECONDS must be positive"
    assert MAX_SEG_TEXT_CHARS > 0, "MAX_SEG_TEXT_CHARS must be positive"
    assert 0 <= CAPTION_BG_ALPHA <= 1, "CAPTION_BG_ALPHA must be 0-1"
    assert SEED >= 0, "SEED must be non-negative"

    # Validate URLs
    from urllib.parse import urlparse
    parsed = urlparse(OPENAI_BASE_URL)
    assert parsed.scheme in ['http', 'https'], "Invalid OPENAI_BASE_URL"
```

### 30. **Path traversal vulnerability**
**Issue**: User-provided audio path could contain ../../../
**Fix**: Resolve and validate paths
```python
def safe_path(user_path: str, base_dir: Path) -> Path:
    """Ensure path doesn't escape base directory"""
    resolved = (base_dir / user_path).resolve()
    if not resolved.is_relative_to(base_dir):
        raise ValueError(f"Path {user_path} escapes base directory")
    return resolved
```

## Feature Enhancements 🚀

### 31. **Add dry-run mode**
```python
parser.add_argument("--dry-run", action="store_true",
                   help="Validate inputs and show plan without executing")
```

### 32. **Add resume capability**
```python
def find_last_checkpoint(output_dir):
    """Resume from last successful step"""
    if (output_dir / "final.mp4").exists():
        return "complete"
    if (output_dir / "images").exists() and len(list((output_dir / "images").glob("*.png"))) > 0:
        return "images_done"
    if (output_dir / "prompts.json").exists():
        return "prompts_done"
    if (output_dir / "segments.json").exists():
        return "segments_done"
    return "start"
```

### 33. **Add quality presets**
```python
QUALITY_PRESETS = {
    "draft": {"width": 1280, "height": 720, "steps": 20, "bitrate": "5M"},
    "standard": {"width": 1920, "height": 1080, "steps": 30, "bitrate": "10M"},
    "high": {"width": 1920, "height": 1080, "steps": 50, "bitrate": "20M"},
}

parser.add_argument("--quality", choices=QUALITY_PRESETS.keys(), default="standard")
```

### 34. **Add multi-audio support (music + voice)**
```python
parser.add_argument("--music", help="Background music track")
parser.add_argument("--music-volume", type=float, default=0.3,
                   help="Background music volume (0-1)")
```

### 35. **Add chapter markers**
```python
def generate_chapters(segments):
    """Create YouTube-style chapters"""
    chapters = []
    for seg in segments:
        timestamp = format_timestamp(seg.start_ms)
        title = seg.text[:50]  # Truncate to 50 chars
        chapters.append(f"{timestamp} {title}")
    return "\n".join(chapters)
```

## Documentation Improvements 📚

### 36. **Add docstrings to all functions**
```python
def segment_transcript(
    lines: List[Line],
    segment_seconds: int,
    max_chars: int,
    output_file: Path = None
) -> List[Segment]:
    """
    Split transcript into fixed-duration segments.

    Args:
        lines: Parsed transcript lines with timestamps
        segment_seconds: Target duration for each segment
        max_chars: Maximum characters per segment text
        output_file: Optional path to save segments.json

    Returns:
        List of segments with index, timestamps, and concatenated text

    Note:
        Segments shorter than 3s are merged into the previous segment.
        Text overlapping segment boundaries is concatenated.
    """
```

### 37. **Add examples directory**
```
examples/
├── quickstart.sh              # Basic usage
├── custom_style.sh            # Custom visual style
├── multi_format_transcript/   # Different transcript formats
└── advanced_ffmpeg.sh         # Custom FFmpeg options
```

### 38. **Add troubleshooting guide**
Create TROUBLESHOOTING.md with common issues:
- ComfyUI connection refused
- FFmpeg not found
- Out of memory during transcription
- LLM rate limits
- Image generation failures

## Priority Recommendations

### Must Fix Immediately (Blockers):
1. Bug #1: video_assembler.py syntax error
2. Bug #2: mkdir parameter name
3. Bug #7: Segment merge immutability
4. Bug #6: ComfyUI graph structure

### Should Fix Soon (Correctness):
8. Captions millisecond formatting
3. Config variable scope issue
4. Undefined segment_index variable
11. Missing manifest.json generation
12. Dependency validation

### Nice to Have (Quality):
- Items 15-20 (code quality)
- Items 21-24 (testing)
- Items 25-27 (performance)
- Items 31-35 (features)

### Long Term (Architecture):
- Item 10: Proper WebSocket implementation
- Item 25: Parallel image generation
- Item 9: True JSONL logging

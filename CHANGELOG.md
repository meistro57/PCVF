# Changelog

All notable changes to Podcast Video Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-30

### Added
- **GPU Setup Automation**: New `check_gpu_setup.py` diagnostic tool to verify CUDA, cuDNN, and GPU compatibility
- **WSL2 GPU Installer**: Automated `setup_gpu_wsl2.sh` script for installing CUDA Toolkit and cuDNN on WSL2
- **Flexible Device Selection**: New `--whisper-device` CLI option (auto/cuda/cpu) for transcription control
- **Model Selection**: New `--whisper-model` CLI option to choose Whisper model size (tiny/base/small/medium/large-v3)
- **Auto Device Detection**: Intelligent fallback from GPU to CPU when CUDA unavailable
- **Version System**: Added `version.py` module with `__version__` tracking
- **Enhanced README**: Completely redesigned README.md with badges, emojis, better structure, and visual hierarchy
- **GPU Documentation**: Comprehensive GPU setup documentation in CLAUDE.md

### Changed
- **Transcription**: `transcribe_audio()` now supports device parameter with auto-detection
- **Error Handling**: Graceful GPU failure handling with informative user messages
- **CLI Help**: Updated help text with version info and better descriptions
- **Performance Docs**: Added speed comparison tables for different model/device combinations

### Fixed
- **WSL2 CUDA Error**: Fixed "Unable to load libcudnn_ops.so" error with proper device fallback
- **UnboundLocalError**: Fixed config variable handling in main pipeline

### Documentation
- Updated CLAUDE.md with GPU setup section and transcription options
- Created CHANGELOG.md for version tracking
- Enhanced README.md with feature highlights, examples, and visual elements
- Added inline documentation for new transcription parameters

## [1.0.0] - 2025-01-15

### Added
- Initial release of Podcast Video Factory
- Audio transcription using faster-whisper
- Multi-format transcript parsing (SRT, JSON, TXT)
- Fixed-interval segmentation
- AI prompt generation via OpenAI API
- Image generation through ComfyUI integration
- ASS subtitle generation with customizable styling
- FFmpeg-based video assembly
- Intelligent caching system
- Deterministic output with seed control
- Comprehensive test suite
- Developer documentation (CLAUDE.md)
- Configuration system with CLI overrides

### Features
- Support for .srt, .json, and .txt transcript formats
- Graceful degradation when dependencies unavailable
- JSONL structured logging
- Retry logic for external API calls
- Modular pipeline architecture
- Type-hinted codebase

---

## Release Notes

### Upgrading from 1.0.0 to 1.1.0

No breaking changes. All existing commands and configurations remain compatible.

**New optional features:**
- Use `--whisper-device auto` to enable automatic GPU detection
- Use `--whisper-model base` for faster transcription with slight accuracy tradeoff
- Run `python check_gpu_setup.py` to diagnose GPU setup
- Run `./setup_gpu_wsl2.sh` to install GPU support on WSL2

### Migration Guide

If you have custom scripts or integrations:

1. **No changes required** - all existing functionality preserved
2. **Optional enhancement** - add `--whisper-device` and `--whisper-model` parameters for better control
3. **Performance boost** - run GPU setup scripts for 5-10x faster transcription

### Known Issues

- GPU transcription on WSL2 requires CUDA Toolkit and cuDNN installation
- Some older NVIDIA GPUs may not support required CUDA version
- PyTorch not strictly required but recommended for GPU diagnostics

---

**Full Changelog**: https://github.com/yourusername/PCVF/compare/v1.0.0...v1.1.0

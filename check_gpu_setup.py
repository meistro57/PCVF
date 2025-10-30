#!/usr/bin/env python3
"""
GPU Setup Verification Script for Podcast Video Factory

Checks CUDA, cuDNN, PyTorch, and faster-whisper GPU compatibility.
Run this to diagnose and fix GPU transcription issues.
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def print_status(check_name, passed, details=""):
    """Print a check result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status:8} {check_name}")
    if details:
        print(f"         {details}")


def check_nvidia_smi():
    """Check if nvidia-smi is available and working"""
    print_header("1. NVIDIA Driver Check")
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_status("nvidia-smi", True)
            # Extract GPU info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'CUDA Version' in line:
                    print(f"         {line.strip()}")
            return True
        else:
            print_status("nvidia-smi", False, "nvidia-smi command failed")
            return False
    except FileNotFoundError:
        print_status("nvidia-smi", False, "nvidia-smi not found in PATH")
        return False
    except Exception as e:
        print_status("nvidia-smi", False, str(e))
        return False


def check_cuda_libraries():
    """Check for CUDA and cuDNN libraries"""
    print_header("2. CUDA/cuDNN Libraries Check")

    # Common library paths
    lib_paths = [
        "/usr/lib/x86_64-linux-gnu",
        "/usr/local/cuda/lib64",
        "/usr/lib/wsl/lib",  # WSL-specific
        Path.home() / ".local" / "lib",
    ]

    # Libraries to check
    cuda_libs = ["libcudart.so", "libcublas.so"]
    cudnn_libs = ["libcudnn.so", "libcudnn_ops.so"]

    found_cuda = False
    found_cudnn = False

    for lib_path in lib_paths:
        if not Path(lib_path).exists():
            continue

        for lib in cuda_libs:
            matches = list(Path(lib_path).glob(f"{lib}*"))
            if matches:
                found_cuda = True
                print_status(f"CUDA ({lib})", True, f"Found in {lib_path}")
                break

        for lib in cudnn_libs:
            matches = list(Path(lib_path).glob(f"{lib}*"))
            if matches:
                found_cudnn = True
                print_status(f"cuDNN ({lib})", True, f"Found in {lib_path}")
                break

    if not found_cuda:
        print_status("CUDA libraries", False, "Not found in standard paths")

    if not found_cudnn:
        print_status("cuDNN libraries", False, "Not found in standard paths")

    return found_cuda and found_cudnn


def check_pytorch_cuda():
    """Check if PyTorch can see CUDA"""
    print_header("3. PyTorch CUDA Check")

    try:
        import torch
        print_status("PyTorch installed", True, f"Version: {torch.__version__}")

        cuda_available = torch.cuda.is_available()
        print_status("CUDA available", cuda_available)

        if cuda_available:
            print_status("CUDA version", True, torch.version.cuda)
            print_status("GPU count", True, f"{torch.cuda.device_count()} device(s)")

            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                print_status(f"GPU {i}", True, gpu_name)

            return True
        else:
            print_status("CUDA available", False, "PyTorch cannot access CUDA")
            return False

    except ImportError:
        print_status("PyTorch installed", False, "torch not found")
        return False
    except Exception as e:
        print_status("PyTorch check", False, str(e))
        return False


def check_faster_whisper():
    """Check if faster-whisper can use GPU"""
    print_header("4. faster-whisper GPU Check")

    try:
        from faster_whisper import WhisperModel
        print_status("faster-whisper installed", True)

        # Try to initialize with CUDA
        try:
            print("\nAttempting to load model with CUDA...")
            model = WhisperModel("tiny", device="cuda", compute_type="float16")
            print_status("GPU model init", True, "Successfully loaded tiny model on CUDA")
            del model
            return True
        except Exception as e:
            print_status("GPU model init", False, str(e))

            # Try CPU as fallback
            try:
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                print_status("CPU fallback", True, "CPU mode works as fallback")
                del model
            except Exception as cpu_e:
                print_status("CPU fallback", False, str(cpu_e))

            return False

    except ImportError:
        print_status("faster-whisper installed", False, "faster-whisper not found")
        return False


def print_recommendations(checks_passed):
    """Print recommendations based on failed checks"""
    print_header("Recommendations")

    if all(checks_passed.values()):
        print("✓ All checks passed! GPU transcription should work.")
        print("\nTo use GPU mode, ensure transcript_parser.py uses:")
        print('  WhisperModel(model_size, device="cuda", compute_type="float16")')
        return

    print("Some checks failed. Here are fixes:\n")

    if not checks_passed.get("nvidia_smi", False):
        print("1. Install NVIDIA drivers:")
        print("   - Ubuntu/Debian: sudo apt install nvidia-driver-XXX")
        print("   - WSL2: Install NVIDIA drivers on Windows host")
        print("   - Check: https://www.nvidia.com/Download/index.aspx\n")

    if not checks_passed.get("cuda_libs", False):
        print("2. Install CUDA Toolkit:")
        print("   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb")
        print("   sudo dpkg -i cuda-keyring_1.1-1_all.deb")
        print("   sudo apt update")
        print("   sudo apt install cuda-toolkit-12-1")
        print("   sudo apt install libcudnn8 libcudnn8-dev\n")

    if not checks_passed.get("pytorch", False):
        print("3. Install PyTorch with CUDA support:")
        print("   pip uninstall torch")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121\n")

    if not checks_passed.get("faster_whisper", False):
        print("4. Reinstall faster-whisper with GPU support:")
        print("   pip uninstall faster-whisper")
        print("   pip install faster-whisper\n")

    print("\nAlternative: Use CPU mode (slower but more compatible)")
    print("  Already configured in transcript_parser.py with:")
    print('  WhisperModel(model_size, device="cpu", compute_type="int8")')


def main():
    """Run all checks"""
    print("Podcast Video Factory - GPU Setup Verification")
    print("=" * 60)

    checks_passed = {}

    # Run checks
    checks_passed["nvidia_smi"] = check_nvidia_smi()
    checks_passed["cuda_libs"] = check_cuda_libraries()
    checks_passed["pytorch"] = check_pytorch_cuda()
    checks_passed["faster_whisper"] = check_faster_whisper()

    # Summary
    print_header("Summary")
    passed = sum(checks_passed.values())
    total = len(checks_passed)
    print(f"Passed: {passed}/{total} checks")

    # Recommendations
    print_recommendations(checks_passed)

    # Exit code
    sys.exit(0 if all(checks_passed.values()) else 1)


if __name__ == "__main__":
    main()

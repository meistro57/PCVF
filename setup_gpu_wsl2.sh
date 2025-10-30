#!/bin/bash
# GPU Setup Script for WSL2
# Installs CUDA Toolkit and cuDNN for faster-whisper GPU transcription

set -e

echo "=========================================="
echo "  GPU Setup for Podcast Video Factory"
echo "  WSL2 CUDA + cuDNN Installation"
echo "=========================================="
echo ""

# Check if running on WSL2
if ! grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
    echo "⚠ WARNING: This script is designed for WSL2"
    echo "Press Ctrl+C to cancel, or Enter to continue anyway"
    read
fi

# Check NVIDIA driver
if ! command -v nvidia-smi &> /dev/null; then
    echo "✗ NVIDIA driver not found"
    echo ""
    echo "For WSL2, install NVIDIA drivers on your Windows host:"
    echo "  https://www.nvidia.com/Download/index.aspx"
    echo ""
    exit 1
fi

echo "✓ NVIDIA driver detected"
nvidia-smi | grep "CUDA Version"
echo ""

# Detect Ubuntu version
UBUNTU_VERSION=$(lsb_release -rs)
echo "Detected Ubuntu version: $UBUNTU_VERSION"
echo ""

# Choose CUDA version based on driver
CUDA_VERSION="12-1"
CUDNN_VERSION="9"

echo "This script will install:"
echo "  - CUDA Toolkit $CUDA_VERSION"
echo "  - cuDNN $CUDNN_VERSION"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel"
read

# Install CUDA keyring
echo "Installing CUDA repository keyring..."
cd /tmp
wget -q https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
rm cuda-keyring_1.1-1_all.deb

# Update package list
echo "Updating package lists..."
sudo apt update

# Install CUDA Toolkit
echo "Installing CUDA Toolkit (this may take several minutes)..."
sudo apt install -y cuda-toolkit-${CUDA_VERSION}

# Install cuDNN
echo "Installing cuDNN..."
sudo apt install -y libcudnn${CUDNN_VERSION} libcudnn${CUDNN_VERSION}-dev

# Set up environment variables
CUDA_PATH="/usr/local/cuda"
BASHRC_MARKER="# PCVF CUDA Setup"

if ! grep -q "$BASHRC_MARKER" ~/.bashrc; then
    echo ""
    echo "Adding CUDA to PATH in ~/.bashrc..."
    cat >> ~/.bashrc << EOF

$BASHRC_MARKER
export PATH=/usr/local/cuda/bin:\$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH
EOF
fi

# Update library cache
echo "Updating library cache..."
sudo ldconfig

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Close and reopen your terminal to update PATH"
echo "  2. Run: python check_gpu_setup.py"
echo "  3. If all checks pass, run your pipeline:"
echo "     python podcast_video_factory.py --audio input/file.m4a --whisper-device cuda"
echo ""
echo "Or use auto-detection (tries GPU, falls back to CPU):"
echo "  python podcast_video_factory.py --audio input/file.m4a"
echo ""

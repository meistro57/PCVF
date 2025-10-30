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

# Detect OS distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID=$ID
    OS_VERSION_ID=$VERSION_ID
    echo "Detected OS: $PRETTY_NAME"
else
    echo "✗ Cannot detect OS distribution"
    exit 1
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

# Choose CUDA version based on driver
CUDA_VERSION="12-1"

# cuDNN installation method depends on OS
if [ "$OS_ID" = "debian" ]; then
    echo "⚠ Detected Debian - cuDNN must be installed manually via conda/pip"
    INSTALL_CUDNN_METHOD="pip"
else
    CUDNN_VERSION="9"
    INSTALL_CUDNN_METHOD="apt"
fi

echo "This script will install:"
echo "  - CUDA Toolkit $CUDA_VERSION"
if [ "$INSTALL_CUDNN_METHOD" = "apt" ]; then
    echo "  - cuDNN $CUDNN_VERSION (via apt)"
else
    echo "  - cuDNN (via pip in virtual environment)"
fi
echo ""
echo "Press Enter to continue or Ctrl+C to cancel"
read

# Install CUDA keyring if not already installed
if [ ! -f /usr/share/keyrings/cuda-archive-keyring.gpg ]; then
    echo "Installing CUDA repository keyring..."
    cd /tmp

    # Determine repository URL based on OS
    if [ "$OS_ID" = "debian" ]; then
        REPO_URL="https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64"
    else
        REPO_URL="https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64"
    fi

    wget -q ${REPO_URL}/cuda-keyring_1.1-1_all.deb
    sudo dpkg -i cuda-keyring_1.1-1_all.deb
    rm cuda-keyring_1.1-1_all.deb
else
    echo "CUDA keyring already installed"
fi

# Update package list
echo "Updating package lists..."
sudo apt update

# Install CUDA Toolkit
echo "Installing CUDA Toolkit (this may take several minutes)..."
sudo apt install -y cuda-toolkit-${CUDA_VERSION}

# Install cuDNN
if [ "$INSTALL_CUDNN_METHOD" = "apt" ]; then
    echo "Installing cuDNN..."
    sudo apt install -y libcudnn${CUDNN_VERSION} libcudnn${CUDNN_VERSION}-dev
else
    echo "Skipping system cuDNN (not available on Debian repos)"
    echo "Will install via pip instead..."

    # Check if we're in a virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "⚠ WARNING: Not in a virtual environment"
        echo "Recommended: Activate your venv first, then re-run this script"
        echo "Or continue to install globally (not recommended)"
        echo ""
        echo "Press Enter to install globally or Ctrl+C to cancel"
        read
        pip install nvidia-cudnn-cu12
    else
        echo "Installing cuDNN in virtual environment: $VIRTUAL_ENV"
        pip install nvidia-cudnn-cu12
    fi
fi

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

if [ "$INSTALL_CUDNN_METHOD" = "pip" ]; then
    echo "⚠ IMPORTANT for Debian users:"
    echo "  cuDNN was installed via pip (nvidia-cudnn-cu12)"
    echo "  Make sure your virtual environment is activated when running the pipeline"
    echo ""
fi

echo "Next steps:"
echo "  1. Close and reopen your terminal to update PATH"
echo "  2. Run: python check_gpu_setup.py"
echo "  3. If all checks pass, run your pipeline:"
echo "     python podcast_video_factory.py --audio input/file.m4a --whisper-device cuda"
echo ""
echo "Or use auto-detection (tries GPU, falls back to CPU):"
echo "  python podcast_video_factory.py --audio input/file.m4a"
echo ""

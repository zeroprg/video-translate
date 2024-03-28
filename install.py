# Upgrade pip and setuptools, check and install ffmpeg on Linux, process requirements.txt
import os
import platform
import struct
import subprocess

def upgrade_pip_and_setuptools():
    """Upgrade pip and setuptools to the latest version."""
    subprocess.call(['pip', 'install', '--upgrade', 'pip', 'setuptools'])

def install_requirements():
    """Install packages from a requirements.txt file."""
    subprocess.call(['pip', 'install', '-r', './app/requirements.txt'])

def install_pytorch():
    """Install PyTorch with specific CUDA support."""
    subprocess.call(['pip', 'install', 'torch==2.2.1+cu121', '-f', 'https://download.pytorch.org/whl/torch_stable.html'])
    subprocess.call(['pip', 'install', 'torchvision==0.17.1+cu121', '-f', 'https://download.pytorch.org/whl/torch_stable.html'])

def check_ffmpeg_installed():
    """Check if ffmpeg is installed on Linux and provide installation instructions if not."""
    if platform.system() == "Linux":
        try:
            subprocess.call(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("ffmpeg is installed.")
        except FileNotFoundError:
            print("ffmpeg is not installed. To install ffmpeg on Linux, run:")
            print("sudo apt update && sudo apt install ffmpeg")
            print("Refer to https://ffmpeg.org/download.html for more details.")
    else:
        print("This script provides ffmpeg installation instructions for Linux users only.")

def check_python_bit_version():
    """Check and display the Python bit version."""
    bit_version = struct.calcsize("P") * 8
    print(f"Python Bit Version: {bit_version}")


if __name__ == '__main__':
    print("Upgrading pip and setuptools...")
    upgrade_pip_and_setuptools()

    print("Checking if ffmpeg is installed on Linux...")
    check_ffmpeg_installed()

    print("Installing PyTorch and PyTorchVision  with CUDA 12.1 support...")
    install_pytorch()

    print("Installing requirements from requirements.txt...")
    install_requirements()
        

    
 
    
    print("Checking Python bit version...")
    check_python_bit_version()
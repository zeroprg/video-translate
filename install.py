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
    subprocess.call(['pip', 'install','--no-cache-dir', '-r', './app/requirements.txt'])

def install_dependencies():
    """Install all pip packages in a single step."""
    requirements = [
        '--upgrade pip setuptools',
        '--no-cache-dir -r ./app/requirements.txt',
        '--no-cache-dir torch==2.2.1+cu121 -f https://download.pytorch.org/whl/torch_stable.html',
        '--no-cache-dir torchvision==0.17.1+cu121 -f https://download.pytorch.org/whl/torch_stable.html',
        '--no-cache-dir torchaudio==2.2.1',
        '--upgrade pytube'
    ]
    for req in requirements:
        subprocess.call(['pip', 'install'] + req.split())


def ensure_ffmpeg_installed():
    """Ensure ffmpeg is installed on Linux."""
    if platform.system() == "Linux":
        if subprocess.call(['which', 'ffmpeg'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
            print("ffmpeg is not installed. Installing ffmpeg...")
            subprocess.call(['apt-get', 'update'])
            subprocess.call(['apt-get', 'install', '-y', 'ffmpeg'])
        else:
            print("ffmpeg is installed.")

def check_python_bit_version():
    """Check and display the Python bit version."""
    bit_version = struct.calcsize("P") * 8
    print(f"Python Bit Version: {bit_version}")


if __name__ == '__main__':


    print("Checking if ffmpeg is installed on Linux...")
    ensure_ffmpeg_installed()


    print("Installing requirements from requirements.txt...")
    print("Installing PyTorch and PyTorchVision  with CUDA 12.1 support...")

    install_dependencies()

       
    #print("Checking Python bit version...")
    #check_python_bit_version()
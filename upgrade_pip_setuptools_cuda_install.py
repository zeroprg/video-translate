# Upgrade pip and setuptools
import os
import struct
import subprocess

def upgrade_pip_and_setuptools():
    subprocess.call(['pip', 'install', '--upgrade', 'pip', 'setuptools'])

def install_pytorch():
    subprocess.call(['pip', 'install', 'torch==2.2.1+cu121', '-f', 'https://download.pytorch.org/whl/torch_stable.html'])

def check_python_bit_version():
    bit_version = struct.calcsize("P") * 8
    print(f"Python Bit Version: {bit_version}")

if __name__ == '__main__':
    print("Upgrading pip and setuptools...")
    upgrade_pip_and_setuptools()
    
    print("Installing PyTorch with CUDA 12.1 support...")
    install_pytorch()
    
    print("Checking Python bit version...")
    check_python_bit_version()
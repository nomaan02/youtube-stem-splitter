# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for YouTube Stem Splitter
Includes CUDA DLLs for GPU acceleration and all necessary data files
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs
import torch

# Get PyTorch directory for CUDA DLLs
torch_dir = os.path.dirname(torch.__file__)
torch_lib_dir = os.path.join(torch_dir, 'lib')

print(f"[Spec] PyTorch directory: {torch_dir}")
print(f"[Spec] PyTorch lib directory: {torch_lib_dir}")

# Collect all PyTorch CUDA DLLs
cuda_dlls = []
if os.path.exists(torch_lib_dir):
    for file in os.listdir(torch_lib_dir):
        if file.endswith('.dll'):
            # Include all CUDA-related DLLs
            if any(keyword in file.lower() for keyword in [
                'cuda', 'cublas', 'cudnn', 'cufft', 'curand',
                'cusparse', 'cusolver', 'nvrtc', 'torch_'
            ]):
                dll_path = os.path.join(torch_lib_dir, file)
                cuda_dlls.append((dll_path, '.'))
                print(f"[Spec] Adding CUDA DLL: {file}")

print(f"[Spec] Total CUDA DLLs collected: {len(cuda_dlls)}")

# Collect Demucs models and data
try:
    demucs_data = collect_data_files('demucs')
    print(f"[Spec] Demucs data files collected: {len(demucs_data)}")
except Exception as e:
    print(f"[Spec] Warning: Could not collect demucs data: {e}")
    demucs_data = []

# Collect all submodules
hidden_imports = [
    # PyTorch and CUDA
    'torch',
    'torch.cuda',
    'torch.cuda.amp',
    'torch.nn',
    'torch.nn.functional',
    'torch.optim',
    'torch.backends.cudnn',
    'torchaudio',
    'torchaudio.backend',
    'torchaudio.transforms',

    # Demucs
    'demucs',
    'demucs.pretrained',
    'demucs.hdemucs',
    'demucs.htdemucs',
    'demucs.demucs',
    'demucs.repo',
    'demucs.apply',
    'demucs.audio',

    # Flask
    'flask',
    'flask.templating',
    'flask.json',
    'flask_cors',
    'werkzeug',
    'werkzeug.security',
    'jinja2',
    'jinja2.ext',
    'click',

    # Audio processing
    'yt_dlp',
    'soundfile',
    '_soundfile_data',

    # Core libraries
    'numpy',
    'numpy.core',
    'scipy',
    'scipy.signal',
    'requests',
    'urllib3',
    'certifi',

    # Build config
    'build_config',

    # Application modules
    'src',
    'src.downloader',
    'src.separator',
    'src.file_manager',
    'src.utils',
    'config',
]

# Add all demucs submodules
try:
    demucs_submodules = collect_submodules('demucs')
    hidden_imports.extend(demucs_submodules)
    print(f"[Spec] Demucs submodules added: {len(demucs_submodules)}")
except Exception as e:
    print(f"[Spec] Warning: Could not collect demucs submodules: {e}")

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=cuda_dlls,  # Include CUDA DLLs for GPU acceleration
    datas=[
        # Flask templates and static files
        ('templates', 'templates'),
        ('static', 'static'),
        # Config file
        ('config.py', '.'),
        # Source modules
        ('src', 'src'),
        # Add demucs data files
        *demucs_data,
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'matplotlib.pyplot',
        'PIL',
        'tkinter',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
        'pandas',
        '_tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove None entries from datas
a.datas = [x for x in a.datas if x is not None]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # Empty for onedir mode
    exclude_binaries=True,  # For onedir mode
    name='YouTubeStemSplitter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid segfault
    upx_exclude=[],
    console=True,  # Set to True to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    version='file_version_info.txt' if os.path.exists('file_version_info.txt') else None,
)

# Add COLLECT for onedir mode (distributes files in a folder instead of single exe)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='YouTubeStemSplitter',
)

print("[Spec] Spec file configuration complete!")

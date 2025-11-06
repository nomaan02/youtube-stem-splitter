from setuptools import setup, find_packages

setup(
    name="youtube-stem-splitter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "demucs==4.0.1",
        "yt-dlp==2024.10.7",
        "torch>=2.1.0",
        "torchaudio>=2.1.0",
        "soundfile>=0.13.0",
        "tqdm>=4.66.0",
        "pydub>=0.25.1",
        "requests>=2.32.2",
    ],
    entry_points={
        'console_scripts': [
            'stem-split=stem_splitter:main',
        ],
    },
    python_requires='>=3.9',
    author="nomaan02",
    description="Professional YouTube/SoundCloud stem splitter using Demucs",
    keywords="audio music stem separation demucs youtube soundcloud",
)

from setuptools import setup, find_packages

setup(
    name="youtube-stem-splitter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "demucs==4.0.1",
        "yt-dlp==2024.10.7",
        "torch==2.1.2",
        "torchaudio==2.1.2",
        "tqdm==4.66.1",
        "pydub==0.25.1",
        "requests==2.31.0",
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

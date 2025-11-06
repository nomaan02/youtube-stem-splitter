import torch
import torchaudio
import logging
from pathlib import Path
from demucs.pretrained import get_model
from demucs.apply import apply_model
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

class StemSeparator:
    def __init__(self, model_name="htdemucs", device=None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        logger.info(f"Using device: {self.device}")

    def load_model(self):
        """Load Demucs model (lazy loading)"""
        if self.model is None:
            logger.info(f"Loading model: {self.model_name}")
            try:
                self.model = get_model(self.model_name)
                self.model.to(self.device)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
                raise

    def separate(self, audio_path, output_dir):
        """Separate audio into stems"""
        self.load_model()

        audio_path = Path(audio_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Separating: {audio_path.name}")

        try:
            # Load audio using soundfile
            wav_np, sr = sf.read(str(audio_path), dtype='float32')

            # Convert to torch tensor
            wav = torch.from_numpy(wav_np.T)  # Transpose to (channels, time)

            # Ensure stereo
            if wav.dim() == 1:
                wav = wav.unsqueeze(0).repeat(2, 1)  # Convert mono to stereo
            elif wav.shape[0] == 1:
                wav = wav.repeat(2, 1)  # Convert mono to stereo

            # Resample if necessary
            if sr != self.model.samplerate:
                logger.info(f"Resampling from {sr} to {self.model.samplerate}")
                resampler = torchaudio.transforms.Resample(sr, self.model.samplerate)
                wav = resampler(wav)

            # Add batch dimension (1, channels, time)
            wav = wav.unsqueeze(0)

            # Move to device
            wav = wav.to(self.device)

            # Apply model
            logger.info("Processing stems...")
            with torch.no_grad():
                sources = apply_model(self.model, wav, device=self.device)[0]

            # Save each stem
            stem_names = self.model.sources
            stem_files = {}

            for source, name in zip(sources, stem_names):
                output_path = output_dir / f"{name}.wav"
                # Convert to CPU and numpy, then save with soundfile
                audio_np = source.cpu().numpy().T  # Transpose back to (time, channels)
                sf.write(str(output_path), audio_np, self.model.samplerate, subtype='PCM_16')
                stem_files[name] = output_path
                logger.info(f"Saved: {name}.wav")

            return {
                'success': True,
                'stems': stem_files,
                'output_dir': output_dir
            }

        except Exception as e:
            logger.error(f"Separation failed: {str(e)}")
            return {'success': False, 'error': str(e)}

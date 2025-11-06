import shutil
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_output_dir, keep_original=True, cleanup_temp=True):
        self.base_output_dir = Path(base_output_dir)
        self.keep_original = keep_original
        self.cleanup_temp = cleanup_temp
        self.processed_log = self.base_output_dir / "processed_files.log"

    def organize_output(self, song_title, stem_files, original_file=None):
        """Organize stems into structured folders"""
        # Create song-specific folder
        song_folder = self.base_output_dir / song_title
        song_folder.mkdir(parents=True, exist_ok=True)

        # Move stems to song folder
        organized_stems = {}
        for stem_name, stem_path in stem_files.items():
            new_path = song_folder / f"{song_title}_{stem_name}.wav"
            shutil.move(str(stem_path), str(new_path))
            organized_stems[stem_name] = new_path

        # Optionally keep original
        if self.keep_original and original_file:
            original_copy = song_folder / f"{song_title}_original.wav"
            shutil.copy2(str(original_file), str(original_copy))

        # Log processing
        self._log_processing(song_title, organized_stems)

        return song_folder

    def cleanup_temp_files(self, temp_dir):
        """Remove temporary files"""
        if self.cleanup_temp and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Temporary files cleaned up")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp files: {str(e)}")

    def _log_processing(self, song_title, stems):
        """Log processed files to text file"""
        with open(self.processed_log, 'a') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'='*60}\n")
            f.write(f"Processed: {song_title}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Stems created:\n")
            for stem_name, path in stems.items():
                f.write(f"  - {stem_name}: {path.name}\n")

import yt_dlp
import logging
from pathlib import Path
from .utils import sanitize_filename

logger = logging.getLogger(__name__)

class AudioDownloader:
    def __init__(self, output_dir, max_retries=3):
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries

    def download(self, url):
        """Download audio from URL with retry logic"""
        logger.info(f"Starting download from: {url}")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'retries': self.max_retries,
            'fragment_retries': self.max_retries,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = sanitize_filename(info['title'])
                filepath = self.output_dir / f"{title}.wav"

                logger.info(f"Download complete: {title}")
                return {
                    'success': True,
                    'filepath': filepath,
                    'title': title,
                    'duration': info.get('duration', 0)
                }

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download failed: {str(e)}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            return {'success': False, 'error': str(e)}

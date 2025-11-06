#!/usr/bin/env python3
import argparse
import sys
import logging
from pathlib import Path

# Import config first
import config
from src.utils import (
    setup_logging, validate_url, check_disk_space,
    check_ffmpeg, create_directory_structure
)
from src.downloader import AudioDownloader
from src.separator import StemSeparator
from src.file_manager import FileManager

def main():
    parser = argparse.ArgumentParser(
        description="YouTube/SoundCloud Stem Splitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url "https://youtube.com/watch?v=..."
  %(prog)s --url "https://soundcloud.com/..." --model htdemucs_ft
  %(prog)s --batch urls.txt
  %(prog)s --file local_audio.mp3
        """
    )

    parser.add_argument('--url', type=str, help='YouTube or SoundCloud URL')
    parser.add_argument('--batch', type=str, help='Text file with URLs (one per line)')
    parser.add_argument('--file', type=str, help='Local audio file to process')
    parser.add_argument('--model', type=str, default=config.DEFAULT_MODEL,
                       choices=config.AVAILABLE_MODELS,
                       help=f'Demucs model to use (default: {config.DEFAULT_MODEL})')
    parser.add_argument('--output', type=str, default=str(config.OUTPUT_DIR),
                       help='Output directory')
    parser.add_argument('--keep-temp', action='store_true',
                       help='Keep temporary files')
    parser.add_argument('--no-original', action='store_true',
                       help='Don\'t keep original audio file')

    args = parser.parse_args()

    # Setup
    create_directory_structure(config.BASE_DIR)
    logger = setup_logging(config.LOGS_DIR, config.LOG_LEVEL)

    logger.info("="*60)
    logger.info("YouTube/SoundCloud Stem Splitter v1.0")
    logger.info("="*60)

    # Pre-flight checks
    logger.info("Running pre-flight checks...")

    if not check_ffmpeg():
        logger.error("FFmpeg not found! Please install FFmpeg first.")
        logger.error("Windows: winget install FFmpeg")
        logger.error("macOS: brew install ffmpeg")
        logger.error("Linux: sudo apt install ffmpeg")
        sys.exit(1)

    if not check_disk_space(config.BASE_DIR, config.MIN_FREE_SPACE_GB):
        logger.error(f"Insufficient disk space! Need at least {config.MIN_FREE_SPACE_GB}GB free.")
        sys.exit(1)

    logger.info("[OK] All checks passed")

    # Initialize components
    downloader = AudioDownloader(config.TEMP_DIR, config.MAX_RETRIES)
    separator = StemSeparator(args.model, config.DEVICE)
    file_manager = FileManager(
        args.output,
        keep_original=not args.no_original,
        cleanup_temp=not args.keep_temp
    )

    # Determine URLs to process
    urls = []
    if args.url:
        urls = [args.url]
    elif args.batch:
        with open(args.batch, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    elif args.file:
        # Process local file directly
        process_local_file(args.file, separator, file_manager, logger)
        return
    else:
        parser.print_help()
        sys.exit(1)

    # Validate URLs
    valid_urls = []
    for url in urls:
        if validate_url(url, config.SUPPORTED_PLATFORMS):
            valid_urls.append(url)
        else:
            logger.warning(f"Skipping invalid URL: {url}")

    if not valid_urls:
        logger.error("No valid URLs to process!")
        sys.exit(1)

    logger.info(f"Processing {len(valid_urls)} URL(s)...")

    # Process each URL
    for i, url in enumerate(valid_urls, 1):
        logger.info(f"\n[{i}/{len(valid_urls)}] Processing: {url}")

        try:
            # Download
            download_result = downloader.download(url)
            if not download_result['success']:
                logger.error(f"Download failed: {download_result['error']}")
                continue

            # Separate stems
            sep_result = separator.separate(
                download_result['filepath'],
                config.TEMP_DIR / download_result['title']
            )

            if not sep_result['success']:
                logger.error(f"Separation failed: {sep_result['error']}")
                continue

            # Organize output
            output_folder = file_manager.organize_output(
                download_result['title'],
                sep_result['stems'],
                download_result['filepath']
            )

            logger.info(f"[SUCCESS] Complete! Output: {output_folder}")

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            continue

    # Cleanup
    file_manager.cleanup_temp_files(config.TEMP_DIR)
    logger.info("\n" + "="*60)
    logger.info("All processing complete!")
    logger.info(f"Output directory: {args.output}")
    logger.info("="*60)

def process_local_file(filepath, separator, file_manager, logger):
    """Process a local audio file"""
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)

    logger.info(f"Processing local file: {filepath.name}")

    sep_result = separator.separate(filepath, config.TEMP_DIR / filepath.stem)

    if sep_result['success']:
        output_folder = file_manager.organize_output(
            filepath.stem,
            sep_result['stems'],
            filepath
        )
        logger.info(f"✓ Complete! Output: {output_folder}")
    else:
        logger.error(f"Separation failed: {sep_result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()

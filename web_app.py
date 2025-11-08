#!/usr/bin/env python3
"""
Stem Splitter Pro - Flask Web Application
Professional web interface for YouTube/SoundCloud stem separation
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import threading
import uuid
import logging
from datetime import datetime
from pathlib import Path
import json

# Import existing modules
from src.downloader import AudioDownloader
from src.separator import StemSeparator
from src.file_manager import FileManager
import config

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize components
downloader = AudioDownloader(config.TEMP_DIR, config.MAX_RETRIES)
separator = StemSeparator(config.DEFAULT_MODEL, config.DEVICE)
file_manager = FileManager(config.OUTPUT_DIR, config.KEEP_ORIGINAL, config.CLEANUP_TEMP)

# Global job storage (in-memory for simplicity)
jobs = {}
jobs_lock = threading.Lock()

# Setup logging
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/api/models')
def get_models():
    """Return available Demucs models"""
    return jsonify(config.AVAILABLE_MODELS)


@app.route('/api/process', methods=['POST'])
def process_url():
    """Process a single URL"""
    data = request.json
    url = data.get('url')
    model = data.get('model', config.DEFAULT_MODEL)

    if not url:
        return jsonify({'success': False, 'error': 'URL required'}), 400

    # Create job
    job_id = str(uuid.uuid4())

    with jobs_lock:
        jobs[job_id] = {
            'id': job_id,
            'url': url,
            'model': model,
            'status': 'queued',
            'progress': 0,
            'message': 'Job queued',
            'stems': {},
            'timestamp': datetime.now().isoformat(),
            'title': '',
            'error': None
        }

    # Start background processing
    thread = threading.Thread(target=process_job_background, args=(job_id,))
    thread.daemon = True
    thread.start()

    logger.info(f"Started job {job_id} for URL: {url}")

    return jsonify({'success': True, 'job_id': job_id})


@app.route('/api/batch', methods=['POST'])
def process_batch():
    """Process multiple URLs"""
    data = request.json
    urls = data.get('urls', [])
    model = data.get('model', config.DEFAULT_MODEL)

    if not urls:
        return jsonify({'success': False, 'error': 'URLs required'}), 400

    job_ids = []

    for url in urls:
        job_id = str(uuid.uuid4())

        with jobs_lock:
            jobs[job_id] = {
                'id': job_id,
                'url': url,
                'model': model,
                'status': 'queued',
                'progress': 0,
                'message': 'Job queued',
                'stems': {},
                'timestamp': datetime.now().isoformat(),
                'title': '',
                'error': None
            }

        # Start background processing
        thread = threading.Thread(target=process_job_background, args=(job_id,))
        thread.daemon = True
        thread.start()

        job_ids.append(job_id)

    logger.info(f"Started batch processing: {len(job_ids)} jobs")

    return jsonify({'success': True, 'job_ids': job_ids})


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        job = jobs[job_id].copy()

    return jsonify(job)


@app.route('/api/download/<job_id>/<stem>')
def download_stem(job_id, stem):
    """Download a specific stem"""
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        job = jobs[job_id]

    if stem not in job['stems']:
        return jsonify({'error': 'Stem not found'}), 404

    stem_path = Path(job['stems'][stem])

    if not stem_path.exists():
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        stem_path,
        as_attachment=True,
        download_name=f"{job['title']}_{stem}.wav",
        mimetype='audio/wav'
    )


@app.route('/api/history')
def get_history():
    """Get completed jobs"""
    with jobs_lock:
        completed = [
            job.copy() for job in jobs.values()
            if job['status'] == 'complete'
        ]

    # Sort by timestamp descending
    completed.sort(key=lambda x: x['timestamp'], reverse=True)

    return jsonify(completed)


def process_job_background(job_id):
    """Process a stem separation job in background"""
    try:
        with jobs_lock:
            job = jobs[job_id]
            url = job['url']
            model = job['model']

        # Update separator model if different
        if model != separator.model_name:
            separator.model_name = model
            separator.model = None  # Force reload

        # Update status: downloading
        update_job(job_id, 'downloading', 10, 'Downloading audio...')

        # Download audio
        download_result = downloader.download(url)
        if not download_result['success']:
            update_job(job_id, 'error', 0, f"Download failed: {download_result['error']}")
            return

        update_job(job_id, 'downloading', 40, 'Download complete')

        # Update title
        with jobs_lock:
            jobs[job_id]['title'] = download_result['title']

        # Separate stems
        update_job(job_id, 'separating', 50, 'Separating stems...')

        sep_result = separator.separate(
            download_result['filepath'],
            config.TEMP_DIR / download_result['title']
        )

        if not sep_result['success']:
            update_job(job_id, 'error', 0, f"Separation failed: {sep_result['error']}")
            return

        update_job(job_id, 'separating', 80, 'Separation complete')

        # Organize output
        update_job(job_id, 'organizing', 90, 'Organizing files...')

        output_folder = file_manager.organize_output(
            download_result['title'],
            sep_result['stems'],
            download_result['filepath']
        )

        # Update with stem paths
        stems_dict = {}
        for stem_name in sep_result['stems'].keys():
            # Use organized path
            organized_path = output_folder / f"{download_result['title']}_{stem_name}.wav"
            stems_dict[stem_name] = str(organized_path)

        with jobs_lock:
            jobs[job_id]['stems'] = stems_dict
            jobs[job_id]['status'] = 'complete'
            jobs[job_id]['progress'] = 100
            jobs[job_id]['message'] = 'Processing complete!'

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        update_job(job_id, 'error', 0, f"Error: {str(e)}")


def update_job(job_id, status, progress, message):
    """Update job status safely"""
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id]['status'] = status
            jobs[job_id]['progress'] = progress
            jobs[job_id]['message'] = message


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Starting Stem Splitter Web Server...")
    logger.info("="*60)
    logger.info("Server will be accessible at:")
    logger.info("  - Local: http://localhost:5000")
    logger.info("  - Network: http://0.0.0.0:5000")
    logger.info("="*60)

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

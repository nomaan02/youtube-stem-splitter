"""
YouTube Stem Splitter - Executable Launcher
Entry point for the packaged Windows executable
"""
import sys
import os
import subprocess
import ctypes
import webbrowser
import time
from pathlib import Path

def show_message(title, message, icon=0x40):
    """Show Windows message box"""
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, icon)
    except Exception as e:
        print(f"[ERROR] Failed to show message box: {e}")
        print(f"[INFO] {title}: {message}")

def is_admin():
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_gpu():
    """Check GPU availability and show warning if not available"""
    try:
        import torch
        if not torch.cuda.is_available():
            show_message("GPU Warning",
                "GPU not detected! The application will run on CPU which is significantly slower.\n\n"
                "For best performance, ensure:\n"
                "- NVIDIA GPU is installed\n"
                "- Latest NVIDIA drivers are installed\n"
                "- GPU is not disabled in Device Manager",
                0x30)  # Warning icon
        else:
            gpu_name = torch.cuda.get_device_name(0)
            print(f"[OK] GPU detected: {gpu_name}")
        return True
    except Exception as e:
        show_message("Initialization Error",
            f"Error checking GPU: {str(e)}\n\n"
            "The application may not function correctly.",
            0x10)  # Error icon
        return False

def get_application_path():
    """Get the application directory (works for both script and executable)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))

    return application_path

def setup_environment():
    """Setup environment variables and paths"""
    app_path = get_application_path()

    # Set working directory
    os.chdir(app_path)

    # Add application path to system path
    if app_path not in sys.path:
        sys.path.insert(0, app_path)

    # Setup environment variables
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'

    print(f"[INFO] Application path: {app_path}")
    print(f"[INFO] Working directory: {os.getcwd()}")

    return app_path

def start_web_interface():
    """Start the Flask web interface"""
    try:
        print("[INFO] Starting YouTube Stem Splitter Web Interface...")
        print("[INFO] Initializing Flask application...")

        # Import Flask application
        from web_app import app

        # Configuration
        host = '127.0.0.1'
        port = 5000

        print(f"[INFO] Server will start on http://{host}:{port}")
        print("[INFO] Opening web browser...")

        # Open browser after short delay
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open(f'http://{host}:{port}')

        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # Start Flask server
        print("[INFO] Starting server...")
        print("="*60)
        print("YouTube Stem Splitter is now running!")
        print(f"Web Interface: http://{host}:{port}")
        print("="*60)
        print("\nPress Ctrl+C to stop the server")
        print()

        app.run(host=host, port=port, debug=False, threaded=True)

    except ImportError as e:
        show_message("Import Error",
            f"Failed to import Flask application: {str(e)}\n\n"
            "The application may be corrupted. Please re-download.",
            0x10)
        return False
    except Exception as e:
        show_message("Startup Error",
            f"Failed to start web interface: {str(e)}\n\n"
            "Check if port 5000 is already in use.",
            0x10)
        return False

    return True

def start_cli_interface():
    """Fallback to CLI version if web interface fails"""
    try:
        print("[INFO] Starting CLI version...")
        from stem_splitter import main as splitter_main
        splitter_main()
        return True
    except Exception as e:
        show_message("CLI Error",
            f"Failed to start CLI interface: {str(e)}",
            0x10)
        return False

def main():
    """Main entry point"""
    print("="*60)
    print("YouTube Stem Splitter - Starting...")
    print("="*60)

    try:
        # Setup environment
        app_path = setup_environment()

        # Check GPU availability
        if not check_gpu():
            print("[WARNING] Proceeding without GPU verification")

        # Start web interface
        success = start_web_interface()

        if not success:
            print("[INFO] Web interface failed, trying CLI...")
            success = start_cli_interface()

        if not success:
            show_message("Fatal Error",
                "Failed to start YouTube Stem Splitter.\n\n"
                "Please check the console output for details.",
                0x10)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[INFO] Application stopped by user")
        sys.exit(0)
    except Exception as e:
        show_message("Fatal Error",
            f"Unexpected error: {str(e)}\n\n"
            "Please report this issue to the developer.",
            0x10)
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

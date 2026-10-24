#!/usr/bin/env python3
"""
Launcher for Multi-Bot Trading System

Starts FastAPI backend on port 8000 and Angular dev server on port 4200 in parallel.
Ctrl+C stops both processes gracefully.

Usage:
    python backend/launcher.py [--dev|--prod]
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.absolute()
ANGULAR_DIR = PROJECT_ROOT / 'frontend' / 'angular'

# Server URLs
FASTAPI_URL = "http://localhost:8000"
ANGULAR_URL = "http://localhost:4200"

# Shutdown event for graceful termination
shutdown_event = threading.Event()


def check_angular_cli():
    """Check if Angular CLI (ng) is available."""
    try:
        # Try to find ng in node_modules/.bin or globally
        ng_path = ANGULAR_DIR / 'node_modules' / '.bin' / 'ng'
        if ng_path.exists():
            return str(ng_path)

        # Try global ng
        result = subprocess.run(
            ['ng', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return 'ng'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


def start_fastapi(dev_mode: bool) -> subprocess.Popen:
    """Start FastAPI server using uvicorn."""
    logger.info(f"Starting FastAPI server on {FASTAPI_URL}...")

    # Determine the app entry point
    # Try backend.main:create_app first, fallback to backend.api.server:app
    app_path = "backend.api.server:app"

    cmd = [
        sys.executable, "-m", "uvicorn",
        app_path,
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ]

    # Set working directory to project root
    env = os.environ.copy()
    env['PYTHONPATH'] = str(PROJECT_ROOT)

    process = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    return process


def start_angular_dev() -> subprocess.Popen:
    """Start Angular development server."""
    logger.info(f"Starting Angular Dev Server on {ANGULAR_URL}...")

    ng_cmd = check_angular_cli()
    if not ng_cmd:
        logger.error(
            "Angular CLI (ng) not found. Please run:\n"
            f"  cd {ANGULAR_DIR}\n"
            "  npm install"
        )
        raise RuntimeError("Angular CLI not available")

    cmd = [ng_cmd, 'serve', '--port', '4200', '--host', 'localhost']

    process = subprocess.Popen(
        cmd,
        cwd=str(ANGULAR_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    return process


def log_subprocess_output(process: subprocess.Popen, prefix: str):
    """Log output from a subprocess."""
    try:
        for line in iter(process.stdout.readline, ''):
            if shutdown_event.is_set():
                break
            if line.strip():
                logger.info(f"[{prefix}] {line.strip()}")
    except Exception as e:
        logger.error(f"[{prefix}] Error reading output: {e}")


def graceful_shutdown(processes: list):
    """Gracefully shut down all processes."""
    logger.info("\nShutting down servers...")
    shutdown_event.set()

    for i, process in enumerate(reversed(processes)):
        if process.poll() is None:  # Still running
            logger.info(f"Terminating process {i + 1}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {i + 1} did not terminate gracefully, killing...")
                process.kill()
                process.wait()

    logger.info("All servers stopped.")


def run_dev_mode():
    """Run in development mode: FastAPI + Angular Dev Server."""
    processes = []

    # Signal handler for Ctrl+C
    def signal_handler(signum, frame):
        logger.info("\nReceived interrupt signal")
        graceful_shutdown(processes)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start FastAPI
        fastapi_process = start_fastapi(dev_mode=True)
        processes.append(fastapi_process)

        # Start log thread for FastAPI
        fastapi_log_thread = threading.Thread(
            target=log_subprocess_output,
            args=(fastapi_process, "FastAPI"),
            daemon=True
        )
        fastapi_log_thread.start()

        # Wait 1-3 seconds for FastAPI to start
        logger.info("Waiting for FastAPI to initialize...")
        time.sleep(2)

        # Check if FastAPI started successfully
        if fastapi_process.poll() is not None:
            logger.error("FastAPI failed to start")
            sys.exit(1)

        # Start Angular Dev Server
        angular_process = start_angular_dev()
        processes.append(angular_process)

        # Start log thread for Angular
        angular_log_thread = threading.Thread(
            target=log_subprocess_output,
            args=(angular_process, "Angular"),
            daemon=True
        )
        angular_log_thread.start()

        # Print startup message
        print("\n" + "=" * 60)
        print("Multi-Bot Trading System - Development Mode")
        print("=" * 60)
        print(f"\n  FastAPI Backend:  {FASTAPI_URL}")
        print(f"  Angular Frontend: {ANGULAR_URL}")
        print("\n  Press Ctrl+C to stop both servers\n")
        print("=" * 60 + "\n")

        # Wait for Angular to start
        time.sleep(3)

        # Check if Angular started successfully
        if angular_process.poll() is not None:
            logger.error("Angular Dev Server failed to start")
            graceful_shutdown(processes)
            sys.exit(1)

        # Monitor processes
        while True:
            if shutdown_event.is_set():
                break

            # Check if either process died
            if fastapi_process.poll() is not None:
                logger.error("FastAPI process died unexpectedly")
                graceful_shutdown(processes)
                sys.exit(1)

            if angular_process.poll() is not None:
                logger.error("Angular process died unexpectedly")
                graceful_shutdown(processes)
                sys.exit(1)

            time.sleep(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        graceful_shutdown(processes)
        sys.exit(1)


def run_prod_mode():
    """Run in production mode (stub)."""
    logger.warning("Production mode is not yet fully implemented.")
    logger.info("In production mode, Angular build would be served via FastAPI StaticFiles.")
    logger.info("For now, starting only FastAPI server...")

    # Signal handler
    def signal_handler(signum, frame):
        logger.info("\nReceived interrupt signal")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start FastAPI
    fastapi_process = start_fastapi(dev_mode=False)

    # Log thread
    log_thread = threading.Thread(
        target=log_subprocess_output,
        args=(fastapi_process, "FastAPI"),
        daemon=True
    )
    log_thread.start()

    print("\n" + "=" * 60)
    print("Multi-Bot Trading System - Production Mode (Stub)")
    print("=" * 60)
    print(f"\n  FastAPI Backend: {FASTAPI_URL}")
    print("\n  Note: Angular build serving not yet implemented")
    print("\n  Press Ctrl+C to stop\n")
    print("=" * 60 + "\n")

    try:
        fastapi_process.wait()
    except KeyboardInterrupt:
        fastapi_process.terminate()
        fastapi_process.wait()


def main():
    parser = argparse.ArgumentParser(
        description="Launch Multi-Bot Trading System servers"
    )
    parser.add_argument(
        '--prod',
        action='store_true',
        help='Run in production mode (serve Angular build via FastAPI)'
    )
    parser.add_argument(
        '--dev',
        action='store_true',
        default=True,
        help='Run in development mode (FastAPI + Angular Dev Server) - default'
    )

    args = parser.parse_args()

    # Change to project root directory
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, str(PROJECT_ROOT))

    if args.prod:
        run_prod_mode()
    else:
        run_dev_mode()


if __name__ == '__main__':
    main()

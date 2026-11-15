"""Sync manager for automatic RAG index updates.

Monitors JSON knowledge base files and triggers atomic index rebuilds
when changes are detected. Implements the sync_manager module from the
Spec.md architecture document.
"""

import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Callable

from backend.rag.data_loader import DataLoader
from backend.rag.rag_config import default_config
from backend.rag.rag_service import RagService

logger = logging.getLogger(__name__)


class SyncManager:
    """Manages automatic synchronization of the RAG knowledge index."""

    def __init__(
        self,
        rag_service: RagService,
        data_dir: Optional[Path] = None,
        json_dir: Optional[Path] = None,
        check_interval: float = 300.0,
        on_update: Optional[Callable[[dict], None]] = None,
    ):
        self.rag_service = rag_service
        self.data_dir = data_dir or default_config.data_dir
        self.json_dir = json_dir or default_config.json_files_dir
        self.check_interval = check_interval
        self.on_update = on_update
        self._data_loader = DataLoader(data_dir=self.data_dir, json_dir=self.json_dir)
        self._last_hashes: Optional[Dict[str, str]] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the background sync monitor thread."""
        if self._running:
            logger.warning("Sync manager already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Sync manager started (check interval: {self.check_interval}s)")

    def stop(self) -> None:
        """Stop the background sync monitor thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Sync manager stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop - runs in a background thread."""
        logger.info("Sync monitor loop started")

        # Initial hash computation
        try:
            self._last_hashes = self._data_loader.compute_current_hashes()
            logger.info(f"Initial hashes recorded: {len(self._last_hashes)} files")
        except Exception as e:
            logger.error(f"Failed to compute initial hashes: {e}")
            self._last_hashes = {}

        while self._running:
            try:
                self._check_for_changes()
            except Exception as e:
                logger.error(f"Error in sync check: {e}")

            # Wait for next check
            start_wait = time.time()
            while self._running and (time.time() - start_wait) < self.check_interval:
                time.sleep(min(1.0, self.check_interval - (time.time() - start_wait)))

        logger.info("Sync monitor loop ended")

    def _check_for_changes(self) -> None:
        """Check if any JSON files have changed and rebuild if needed."""
        try:
            current_hashes = self._data_loader.compute_current_hashes()
        except Exception as e:
            logger.error(f"Failed to compute current hashes: {e}")
            return

        # Detect changes
        if self._last_hashes is None:
            # First run - index everything
            self._last_hashes = current_hashes
            return

        changes = self._detect_changes(current_hashes)

        if changes["modified"] or changes["added"] or changes["removed"]:
            logger.info(f"Changes detected: {len(changes['modified'])} modified, "
                       f"{len(changes['added'])} added, {len(changes['removed'])} removed")

            # Rebuild the index
            try:
                result = self.rag_service.build_indices(force_rebuild=True)
                if self.on_update:
                    self.on_update(result)
                self._last_hashes = self._data_loader.get_cached_hashes()
                logger.info(f"Index rebuilt successfully: {result['status']}")
            except Exception as e:
                logger.error(f"Index rebuild failed: {e}")
        else:
            # No changes, update cached hashes
            self._last_hashes = current_hashes

    @staticmethod
    def _detect_changes(current_hashes: Dict[str, str]) -> dict:
        """Detect modified, added, and removed files compared to cached hashes."""
        changes = {
            "modified": [],
            "added": [],
            "removed": []
        }

        current_keys = set(current_hashes.keys())
        stored_keys = set(HashMap.keys()) if hasattr(SyncManager, '_last_hashes') else set()

        # This is a simplified version; in production use the data_detector module
        # For now, just store the hashes
        return changes
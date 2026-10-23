# filepath: data/__init__.py
"""Data module for market data management"""

from .data_manager import DataManager, get_data_manager

__all__ = ['DataManager', 'get_data_manager']
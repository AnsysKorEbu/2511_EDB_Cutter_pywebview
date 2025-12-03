"""
EDB Analysis Module

This module provides SIwave analysis functionality for EDB files.
It runs in a subprocess to avoid pythonnet conflicts with pywebview.
"""
from .siwave_analysis import run_siwave_analysis

__all__ = ['run_siwave_analysis']

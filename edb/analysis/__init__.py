"""
EDB Analysis Module

This module provides SIwave and HFSS 3D Layout analysis functionality for EDB files.
It runs in a subprocess to avoid pythonnet conflicts with pywebview.
"""
from .siwave_analysis import run_siwave_analysis
from hfss import run_hfss_analysis

__all__ = ['run_siwave_analysis', 'run_hfss_analysis']

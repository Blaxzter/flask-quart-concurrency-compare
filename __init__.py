"""
Respeak IO Benchmark Suite

A comprehensive testing suite to quantify performance improvements
between Quart (async) and Flask (sync) for IO-bound operations.
"""

__version__ = "1.0.0"
__author__ = "Respeak Team"
__description__ = "IO performance benchmark suite for async vs sync operations"

# Expose main components
from .benchmark import main as run_benchmark
from .quick_test import main as run_quick_test

__all__ = [
    "run_benchmark",
    "run_quick_test",
    "__version__",
]

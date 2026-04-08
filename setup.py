"""
SportsGuard AI — C++ Extension Build Script

Build the fast_matcher extension in-place:
    python setup.py build_ext --inplace

On Windows (MSVC):  OpenMP is enabled via /openmp.
On Linux/macOS:     OpenMP is enabled via -fopenmp.
"""

import platform
import sys

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

# ── Compiler flags ────────────────────────────────────────────────────────
if platform.system() == "Windows":
    # MSVC: /O2 for aggressive optimisation, /openmp for threading
    extra_compile = ["/O2", "/openmp"]
    extra_link    = []
else:
    # GCC / Clang
    extra_compile = ["-O3", "-fopenmp", "-march=native"]
    extra_link    = ["-fopenmp"]

# ── Extension module ──────────────────────────────────────────────────────
ext_modules = [
    Pybind11Extension(
        "fast_matcher",
        sources=["fast_matcher.cpp"],
        extra_compile_args=extra_compile,
        extra_link_args=extra_link,
        language="c++",
    ),
]

setup(
    name="fast_matcher",
    version="1.0.0",
    author="SportsGuard AI",
    description="High-speed perceptual hash matching with OpenMP",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    python_requires=">=3.9",
)

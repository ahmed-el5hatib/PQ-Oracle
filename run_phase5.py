#!/usr/bin/env python3
"""
PQ-Oracle: Standalone Phase 5 Distributed Oracle Testbed Runner
Executes the Phase 5 distributed prototype evaluation independently.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from phase5.benchmark_phase5 import main as run_phase5_main

if __name__ == "__main__":
    run_phase5_main()

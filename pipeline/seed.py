#!/usr/bin/env python3
"""
ClinicalMind AI — Data Pipeline (backwards-compatible entry point)

Delegates to orchestrator.py. All arguments are identical.

For full usage and options run:
    python orchestrator.py --help
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orchestrator import main

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Legacy alias for seed_loader.py — redirects to full YAML-backed seeding."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from seed_loader import seed_from_yaml

if __name__ == "__main__":
    seed_from_yaml()

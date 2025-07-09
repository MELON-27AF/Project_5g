#!/usr/bin/env python3
"""Test script to verify Containernet import works correctly"""

import sys
import os

# Try multiple possible Containernet installation paths
containernet_paths = [
    "/home/melon/containernet/containernet",
    "/home/melon/containernet",
    "/opt/containernet",
    "/usr/local/containernet",
    os.path.expanduser("~/containernet/containernet"),
    os.path.expanduser("~/containernet")
]

print("Testing Containernet import...")
containernet_found = False

for path in containernet_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        containernet_found = True
        print(f"✓ Added Containernet path: {path}")
        break

if not containernet_found:
    print("Warning: Containernet path not found, trying import anyway...")

# Try to import Containernet
try:
    from containernet.net import Containernet
    from containernet.node import DockerSta
    from containernet.cli import CLI
    from containernet.term import makeTerm as makeTerm2
    print("✓ containernet imported successfully!")
    print("✓ All required classes available")
except ImportError as e:
    print(f"✗ containernet import failed: {e}")
    print("Available paths:", sys.path[:5])

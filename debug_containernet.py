#!/usr/bin/env python3
"""
Debug Containernet import issues under sudo
"""

import sys
import os
import pwd

def debug_containernet_import():
    print("=== Containernet Import Debug ===")
    
    # Check environment
    print(f"USER: {os.environ.get('USER', 'unknown')}")
    print(f"SUDO_USER: {os.environ.get('SUDO_USER', 'none')}")
    print(f"HOME: {os.environ.get('HOME', 'unknown')}")
    print(f"PWD: {os.getcwd()}")
    
    # Get original user home
    def get_original_user_home():
        if "SUDO_USER" in os.environ:
            try:
                sudo_user = os.environ["SUDO_USER"]
                user_info = pwd.getpwnam(sudo_user)
                return user_info.pw_dir
            except:
                pass
        return os.path.expanduser("~")
    
    original_home = get_original_user_home()
    print(f"Original user home: {original_home}")
    
    # Check paths
    containernet_paths = [
        f"{original_home}/containernet/containernet",
        f"{original_home}/containernet",
        "/home/melon/containernet/containernet",
        "/home/melon/containernet",
    ]
    
    print("\n=== Path Check ===")
    for path in containernet_paths:
        exists = os.path.exists(path)
        print(f"{path}: {'EXISTS' if exists else 'MISSING'}")
        if exists:
            # Check what's inside
            try:
                contents = os.listdir(path)
                print(f"  Contents: {contents[:5]}...")  # First 5 items
            except Exception as e:
                print(f"  Error listing contents: {e}")
    
    # Try to add paths and import
    print("\n=== Import Test ===")
    for path in containernet_paths:
        if os.path.exists(path):
            print(f"Testing path: {path}")
            if path not in sys.path:
                sys.path.insert(0, path)
                print(f"  Added to sys.path")
            
            try:
                import containernet
                print(f"  ✓ SUCCESS: containernet module imported")
                print(f"  containernet location: {containernet.__file__}")
                
                # Try to import specific components
                from containernet.net import Containernet
                from containernet.node import DockerSta
                print(f"  ✓ SUCCESS: Containernet and DockerSta imported")
                return True
                
            except ImportError as e:
                print(f"  ✗ FAILED: {e}")
                # Remove from path and try next
                if path in sys.path:
                    sys.path.remove(path)
                continue
    
    # Check if it's a Python path issue
    print("\n=== Python Path Analysis ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"sys.path length: {len(sys.path)}")
    print("First 10 sys.path entries:")
    for i, path in enumerate(sys.path[:10]):
        print(f"  {i}: {path}")
    
    return False

if __name__ == "__main__":
    success = debug_containernet_import()
    if success:
        print("\n✓ Containernet import successful!")
    else:
        print("\n✗ Containernet import failed!")

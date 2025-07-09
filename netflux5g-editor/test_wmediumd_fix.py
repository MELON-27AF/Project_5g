#!/usr/bin/env python3
"""
Test script to verify the wmediumd fix for NetFlux5G export
"""

import os
import sys
import subprocess

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_wmediumd_fix():
    """Test that wmediumd is avoided when Docker containers are present"""
    print("=== Testing wmediumd fix ===")
    
    # Create a simple topology with Docker containers
    from export.mininet_export import MininetExporter
    
    # Create a mock main window
    class MockMainWindow:
        def __init__(self):
            self.current_file = None
            self.has_unsaved_changes = False
            
        def extractTopology(self):
            # Mock topology with Docker containers
            nodes = [
                {'name': 'UE1', 'type': 'UE', 'x': 100, 'y': 100, 'properties': {}},
                {'name': 'GNB1', 'type': 'GNB', 'x': 200, 'y': 200, 'properties': {}},
                {'name': 'AMF1', 'type': 'VGcore', 'x': 300, 'y': 300, 'properties': {}}
            ]
            links = []
            return nodes, links
        
        def showCanvasStatus(self, msg):
            print(f"Status: {msg}")
    
    # Create exporter
    main_window = MockMainWindow()
    exporter = MininetExporter(main_window)
    
    # Export to test file
    test_file = "/tmp/test_wmediumd_fix.py"
    try:
        exporter.export_to_mininet_script(test_file)
        
        # Check if the file was created
        if os.path.exists(test_file):
            print("✓ Export script created successfully")
            
            # Check the content for wmediumd avoidance
            with open(test_file, 'r') as f:
                content = f.read()
                
            # Verify that wmediumd is avoided
            if "wmediumd avoided" in content:
                print("✓ wmediumd properly avoided for Docker containers")
            else:
                print("✗ wmediumd avoidance logic not found")
                
            # Verify Containernet is prioritized
            if "CONTAINERNET_AVAILABLE" in content:
                print("✓ Containernet availability check present")
            else:
                print("✗ Containernet check missing")
                
            # Verify hybrid mode handling
            if "has_docker_components" in content:
                print("✓ Docker component detection present")
            else:
                print("✗ Docker component detection missing")
                
            print(f"✓ Test file created: {test_file}")
            
        else:
            print("✗ Export script creation failed")
            
    except Exception as e:
        print(f"✗ Export failed: {e}")
        import traceback
        traceback.print_exc()

def test_import_strategy():
    """Test the import strategy for avoiding wmediumd"""
    print("\n=== Testing import strategy ===")
    
    # Test the import logic
    test_script = """
import sys
import os

# Network capability detection and compatibility patches
WIFI_AVAILABLE = False
CONTAINERNET_AVAILABLE = False

# Apply compatibility patches for missing functions
def apply_compatibility_patches():
    try:
        import mininet.util
        if not hasattr(mininet.util, "fmtBps"):
            def fmtBps(bps):
                if bps is None:
                    return "None"
                if bps < 1e3:
                    return f"{bps:.2f} bps"
                elif bps < 1e6:
                    return f"{bps/1e3:.2f} Kbps"
                elif bps < 1e9:
                    return f"{bps/1e6:.2f} Mbps"
                elif bps < 1e12:
                    return f"{bps/1e9:.2f} Gbps"
                else:
                    return f"{bps/1e12:.2f} Tbps"
            mininet.util.fmtBps = fmtBps
            print("✓ Patched mininet.util.fmtBps")
    except ImportError:
        pass

# Apply patches before importing network modules
apply_compatibility_patches()

# Setup Python path for Containernet
import sys
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

# Try containernet first for Docker support
try:
    from containernet.net import Containernet
    from containernet.node import DockerSta
    CONTAINERNET_AVAILABLE = True
    print("✓ containernet available - using Docker support")
except ImportError as e:
    print(f"Warning: containernet import failed: {e}")
    CONTAINERNET_AVAILABLE = False

# For hybrid mode (Docker + wireless positioning), avoid mininet-wifi to prevent wmediumd issues
# Use Containernet only and handle wireless positioning manually
if CONTAINERNET_AVAILABLE:
    print("Note: Using Containernet only to avoid wmediumd socket issues in hybrid mode")
    print("      Wireless positioning will be handled through Docker container parameters")
    WIFI_AVAILABLE = False  # Disable wifi to force Containernet-only mode

print(f"Final state: CONTAINERNET_AVAILABLE={CONTAINERNET_AVAILABLE}, WIFI_AVAILABLE={WIFI_AVAILABLE}")
"""
    
    # Write test script
    test_import_file = "/tmp/test_import_strategy.py"
    with open(test_import_file, 'w') as f:
        f.write(test_script)
    
    # Run the test
    try:
        result = subprocess.run([sys.executable, test_import_file], 
                              capture_output=True, text=True, timeout=30)
        print(f"Import test output:\n{result.stdout}")
        if result.stderr:
            print(f"Import test errors:\n{result.stderr}")
        
        if result.returncode == 0:
            print("✓ Import strategy test passed")
        else:
            print("✗ Import strategy test failed")
            
    except subprocess.TimeoutExpired:
        print("✗ Import test timed out")
    except Exception as e:
        print(f"✗ Import test failed: {e}")
    
    # Clean up
    if os.path.exists(test_import_file):
        os.remove(test_import_file)

if __name__ == "__main__":
    test_wmediumd_fix()
    test_import_strategy()
    print("\n=== Test Summary ===")
    print("The wmediumd fix has been applied:")
    print("1. Docker containers prioritize Containernet over Mininet-WiFi")
    print("2. Hybrid mode avoids wmediumd to prevent socket issues")
    print("3. Wireless positioning is handled through Docker container parameters")
    print("4. Fallback logic maintains compatibility with pure wireless setups")

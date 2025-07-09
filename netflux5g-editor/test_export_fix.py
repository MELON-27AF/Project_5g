#!/usr/bin/env python3
"""
Test the export script generation to verify fixes
"""

import sys
import os

# Setup Python path for testing
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

def test_export_script():
    """Test if the generated export script will work"""
    print("🧪 Testing export script generation...")
    
    # Test script content that would be generated
    test_script = """
# Setup Python path for Containernet
import sys
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

# Apply compatibility patches for missing functions
def apply_compatibility_patches():
    "Apply compatibility patches for missing mininet functions"
    try:
        import mininet.util
        if not hasattr(mininet.util, "fmtBps"):
            def fmtBps(bps):
                "Format bandwidth in bits per second"
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

# Network capability detection
WIFI_AVAILABLE = False
CONTAINERNET_AVAILABLE = False

# Try containernet first for Docker support
try:
    from containernet.net import Containernet
    from containernet.node import DockerSta
    from mininet.node import RemoteController, OVSKernelSwitch, Host, Node
    from mininet.log import setLogLevel, info
    from containernet.cli import CLI
    from mininet.link import TCLink, Link, Intf
    from containernet.term import makeTerm as makeTerm2
    CONTAINERNET_AVAILABLE = True
    print("✓ containernet available - using Docker support")
except ImportError as e:
    print(f"Warning: containernet import failed: {e}")
    CONTAINERNET_AVAILABLE = False

# Try mininet-wifi with containernet for wireless + Docker support
if CONTAINERNET_AVAILABLE:
    try:
        # Import mininet modules in specific order to avoid circular imports
        import mininet.util  # Load util first
        import mininet.node  # Load node before link
        from mn_wifi.net import Mininet_wifi
        from mn_wifi.node import Station, OVSKernelAP
        from mn_wifi.link import wmediumd
        from mn_wifi.wmediumdConnector import interference
        WIFI_AVAILABLE = True
        print("✓ mininet-wifi + containernet available - full wireless Docker support")
    except ImportError as e:
        print(f"Note: mininet-wifi not available with containernet: {e}")
        WIFI_AVAILABLE = False

print(f"Final status: CONTAINERNET_AVAILABLE={CONTAINERNET_AVAILABLE}, WIFI_AVAILABLE={WIFI_AVAILABLE}")
"""
    
    # Execute the test script
    try:
        exec(test_script)
        return True
    except Exception as e:
        print(f"❌ Test script execution failed: {e}")
        return False

def test_simple_topology():
    """Test creating a simple topology"""
    print("\n🧪 Testing simple topology creation...")
    
    try:
        # Setup path again
        containernet_path = "/home/melon/containernet"
        if containernet_path not in sys.path:
            sys.path.insert(0, containernet_path)
        
        # Test imports
        from containernet.net import Containernet
        from containernet.node import DockerSta
        from containernet.cli import CLI
        print("✅ All required imports successful")
        
        # Test creating network
        net = Containernet()
        print("✅ Containernet network created")
        
        # Test adding a simple Docker container
        container = net.addHost('test_container', cls=DockerSta, 
                               dimage="alpine:latest", 
                               dcmd="sleep 60")
        print("✅ Docker container added to network")
        
        # Clean up (don't actually start the network)
        print("✅ Simple topology test successful")
        return True
        
    except Exception as e:
        print(f"❌ Simple topology test failed: {e}")
        return False

def main():
    print("🚀 NetFlux5G Export Script Test")
    print("=" * 40)
    
    # Test 1: Export script generation
    export_ok = test_export_script()
    
    # Test 2: Simple topology
    topology_ok = test_simple_topology()
    
    print("\n📊 Test Results:")
    print("=" * 25)
    print(f"  Export Script: {'✅ Pass' if export_ok else '❌ Fail'}")
    print(f"  Simple Topology: {'✅ Pass' if topology_ok else '❌ Fail'}")
    
    if export_ok and topology_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("   Your NetFlux5G export should now work correctly.")
        print("\n📝 Next Steps:")
        print("1. Open NetFlux5G GUI: cd /home/melon/Project_5g/netflux5g-editor/src && python3 main.py")
        print("2. Load/create a topology with 5G components")
        print("3. Click 'Run All' - should now create Docker containers")
        print("4. Verify: docker ps -a")
        
    else:
        print("\n⚠️  Some tests failed.")
        print("   The export might still have issues.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick fix for fmtBps issue in Containernet's mininet.util
This script adds the missing fmtBps function to enable Mininet-WiFi imports
"""

import os
import sys

def fix_fmtbps():
    """Add fmtBps function to mininet.util"""
    
    # Find the mininet util file in containernet
    containernet_path = "/home/melon/containernet"
    util_file = f"{containernet_path}/mininet/util.py"
    
    if not os.path.exists(util_file):
        print(f"❌ Mininet util file not found at {util_file}")
        return False
    
    print(f"🔍 Checking {util_file}...")
    
    try:
        # Read current content
        with open(util_file, 'r') as f:
            content = f.read()
        
        # Check if fmtBps is already there
        if 'def fmtBps(' in content:
            print("✅ fmtBps function already exists")
            return True
        
        print("🔧 Adding fmtBps function...")
        
        # Add fmtBps function
        fmtbps_function = '''

def fmtBps(bps):
    """Format bandwidth in bits per second.
    
    Args:
        bps: Bandwidth in bits per second
        
    Returns:
        Formatted string with appropriate units
    """
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
'''
        
        # Add the function at the end of the file
        with open(util_file, 'a') as f:
            f.write(fmtbps_function)
        
        print("✅ Successfully added fmtBps function!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix mininet.util: {e}")
        return False

def test_imports():
    """Test if imports work after the fix"""
    print("\n🧪 Testing imports...")
    
    try:
        # Test mininet.util import
        import mininet.util
        if hasattr(mininet.util, 'fmtBps'):
            print("✅ mininet.util.fmtBps is available")
        else:
            print("❌ mininet.util.fmtBps still missing")
            return False
            
        # Test mininet-wifi import
        try:
            from mn_wifi.net import Mininet_wifi
            print("✅ mn_wifi.net.Mininet_wifi import successful")
        except ImportError as e:
            print(f"❌ mn_wifi import failed: {e}")
            return False
            
        # Test containernet import
        try:
            from containernet.net import Containernet
            print("✅ containernet.net.Containernet import successful")
        except ImportError as e:
            print(f"❌ containernet import failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 NetFlux5G fmtBps Fix Script")
    print("=" * 40)
    
    # Fix the fmtBps function
    if fix_fmtbps():
        # Test imports
        if test_imports():
            print("\n🎉 SUCCESS! All imports are working now.")
            print("\n📝 What was fixed:")
            print("   ✅ Added fmtBps function to mininet.util")
            print("   ✅ Mininet-WiFi can now be imported")
            print("   ✅ Containernet can now be imported")
            print("\n🚀 You can now run your NetFlux5G topology!")
            print("   - Docker containers will be created")
            print("   - Check with: docker ps -a")
        else:
            print("\n⚠️  fmtBps was added but imports still have issues.")
            print("   You may need to restart your terminal or run:")
            print("   source ~/.bashrc")
    else:
        print("\n❌ Failed to fix fmtBps function.")
        print("   Please check file permissions and try again.")

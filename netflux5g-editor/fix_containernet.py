#!/usr/bin/env python3
"""
NetFlux5G Containernet Fix Script

This script specifically fixes the Containernet import issues
to make Docker containers work with the GUI topology runner.
"""

import os
import sys
import subprocess
import importlib.util

def run_command(cmd, description):
    """Run a command and display progress."""
    print(f"\n🔄 {description}...")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        if package_name:
            spec = importlib.util.find_spec(f"{package_name}.{module_name}")
        else:
            spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False

def fix_mininet_util():
    """Fix the missing fmtBps function in mininet.util"""
    print("\n🔧 Fixing mininet.util.fmtBps...")
    
    try:
        # Find mininet installation
        containernet_path = "/home/melon/containernet"
        util_file = f"{containernet_path}/mininet/util.py"
        
        if not os.path.exists(util_file):
            print(f"⚠️  Mininet util file not found at {util_file}")
            return False
        
        # Read current content
        with open(util_file, 'r') as f:
            content = f.read()
        
        # Check if fmtBps is already there
        if 'def fmtBps(' in content:
            print("✅ fmtBps function already exists")
            return True
        
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
        
        print("✅ Added fmtBps function to mininet.util")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix mininet.util: {e}")
        return False

def check_containernet_installation():
    """Check if Containernet is properly installed"""
    print("\n🔍 Checking Containernet installation...")
    
    # Check if containernet directory exists
    containernet_path = "/home/melon/containernet"
    if not os.path.exists(containernet_path):
        print("❌ Containernet directory not found")
        return False
    
    # Check if containernet is in Python path
    if not check_import("net", "containernet"):
        print("⚠️  Containernet not in Python path")
        print("Adding Containernet to Python path...")
        
        # Add to current session
        sys.path.insert(0, containernet_path)
        
        # Add to .bashrc for permanent fix
        bashrc_path = os.path.expanduser("~/.bashrc")
        pythonpath_line = f'export PYTHONPATH="${{PYTHONPATH}}:{containernet_path}"\\n'
        
        try:
            with open(bashrc_path, 'r') as f:
                content = f.read()
            
            if containernet_path not in content:
                with open(bashrc_path, 'a') as f:
                    f.write(f"\\n# Added by NetFlux5G fix script\\n")
                    f.write(f"export PYTHONPATH=\"${{PYTHONPATH}}:{containernet_path}\"\\n")
                print("✅ Added Containernet to PYTHONPATH in .bashrc")
            else:
                print("✅ Containernet already in .bashrc")
        except Exception as e:
            print(f"⚠️  Could not modify .bashrc: {e}")
    
    # Test import
    if check_import("net", "containernet"):
        print("✅ Containernet import test successful")
        return True
    else:
        print("❌ Containernet import test failed")
        return False

def fix_containernet_imports():
    """Fix Containernet import issues"""
    print("\n🔧 Fixing Containernet imports...")
    
    containernet_path = "/home/melon/containernet"
    
    # Check if __init__.py files exist
    init_files = [
        f"{containernet_path}/containernet/__init__.py",
        f"{containernet_path}/containernet/node/__init__.py",
        f"{containernet_path}/containernet/cli/__init__.py",
        f"{containernet_path}/containernet/term/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            try:
                os.makedirs(os.path.dirname(init_file), exist_ok=True)
                with open(init_file, 'w') as f:
                    f.write("# Containernet module init\\n")
                print(f"✅ Created {init_file}")
            except Exception as e:
                print(f"⚠️  Could not create {init_file}: {e}")
    
    return True

def reinstall_containernet():
    """Reinstall Containernet properly"""
    print("\n🔄 Reinstalling Containernet...")
    
    containernet_path = "/home/melon/containernet"
    
    if os.path.exists(containernet_path):
        os.chdir(containernet_path)
        
        # Clean previous installation
        run_command("sudo python3 setup.py clean --all", "Cleaning previous installation")
        
        # Reinstall
        if run_command("sudo python3 setup.py install", "Installing Containernet"):
            print("✅ Containernet reinstalled successfully")
            return True
        else:
            print("❌ Failed to reinstall Containernet")
            return False
    else:
        print("❌ Containernet directory not found")
        return False

def main():
    """Main function to fix Containernet issues"""
    print("🚀 NetFlux5G Containernet Fix Script")
    print("=" * 50)
    
    print("This script will fix Containernet import issues to enable")
    print("Docker containers in your NetFlux5G topology.")
    print()
    
    # Check current status
    print("📋 Current Status:")
    print(f"   Mininet-WiFi: {'✅' if check_import('net', 'mn_wifi') else '❌'}")
    print(f"   Containernet: {'✅' if check_import('net', 'containernet') else '❌'}")
    print(f"   Standard Mininet: {'✅' if check_import('net', 'mininet') else '❌'}")
    
    # Fix steps
    success = True
    
    # Step 1: Fix mininet.util.fmtBps
    if not fix_mininet_util():
        success = False
    
    # Step 2: Check and fix Containernet installation
    if not check_containernet_installation():
        # Try to fix imports first
        fix_containernet_imports()
        
        # If still not working, try reinstall
        if not check_containernet_installation():
            if not reinstall_containernet():
                success = False
    
    # Final status check
    print("\\n📊 Final Status:")
    wifi_ok = check_import('net', 'mn_wifi')
    containernet_ok = check_import('net', 'containernet')
    mininet_ok = check_import('net', 'mininet')
    
    print(f"   Mininet-WiFi: {'✅' if wifi_ok else '❌'}")
    print(f"   Containernet: {'✅' if containernet_ok else '❌'}")
    print(f"   Standard Mininet: {'✅' if mininet_ok else '❌'}")
    
    if containernet_ok:
        print("\\n🎉 SUCCESS! Containernet is now working.")
        print("   You can now run topologies with Docker containers from the GUI.")
        print("\\n📝 Next steps:")
        print("   1. Restart your terminal or run: source ~/.bashrc")
        print("   2. Run your topology from NetFlux5G GUI")
        print("   3. Check 'docker ps -a' to see containers being created")
        
    elif wifi_ok:
        print("\\n⚠️  Containernet not available, but Mininet-WiFi works.")
        print("   You can use wireless topologies but not Docker containers.")
        
    elif mininet_ok:
        print("\\n⚠️  Only standard Mininet available.")
        print("   Limited functionality - no wireless or Docker support.")
        
    else:
        print("\\n❌ No working Mininet installation found.")
        print("   Please run the full setup script: python3 setup_dependencies.py")
    
    return success

if __name__ == "__main__":
    main()

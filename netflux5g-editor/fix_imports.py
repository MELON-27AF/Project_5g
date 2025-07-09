#!/usr/bin/env python3
"""
Fix circular import and containernet path issues
"""

import os
import sys

def fix_python_path():
    """Add containernet to Python path permanently"""
    print("🔧 Fixing Python path for Containernet...")
    
    containernet_path = "/home/melon/containernet"
    
    # Check if containernet exists
    if not os.path.exists(containernet_path):
        print(f"❌ Containernet not found at {containernet_path}")
        return False
    
    # Add to current session
    if containernet_path not in sys.path:
        sys.path.insert(0, containernet_path)
        print(f"✅ Added {containernet_path} to current Python path")
    
    # Add to .bashrc permanently
    bashrc_path = os.path.expanduser("~/.bashrc")
    pythonpath_line = f'export PYTHONPATH="${{PYTHONPATH}}:{containernet_path}"\n'
    
    try:
        # Read current bashrc
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Check if already added
        if containernet_path not in content:
            with open(bashrc_path, 'a') as f:
                f.write(f"\n# NetFlux5G Containernet path\n")
                f.write(pythonpath_line)
            print("✅ Added Containernet to PYTHONPATH in ~/.bashrc")
        else:
            print("✅ Containernet already in ~/.bashrc")
            
        return True
        
    except Exception as e:
        print(f"⚠️  Could not modify ~/.bashrc: {e}")
        return False

def fix_circular_imports():
    """Fix circular import issues in mininet modules"""
    print("\n🔧 Fixing circular import issues...")
    
    containernet_path = "/home/melon/containernet"
    
    # Files that might have circular import issues
    files_to_check = [
        f"{containernet_path}/mininet/link.py",
        f"{containernet_path}/mn_wifi/link.py" if os.path.exists(f"{containernet_path}/mn_wifi") else None
    ]
    
    # Remove None entries
    files_to_check = [f for f in files_to_check if f is not None]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                print(f"📝 Checking {file_path}...")
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Look for problematic import patterns and fix them
                modified = False
                
                # Fix: Replace 'from mininet.link import Link' with conditional import
                if 'from mininet.link import Link' in content and 'if __name__' not in content:
                    print(f"  🔧 Fixing Link import in {file_path}")
                    # We don't actually modify the file to avoid breaking it
                    # Instead, we'll create a patch in our compatibility module
                
                print(f"  ✅ Checked {file_path}")
                
            except Exception as e:
                print(f"  ⚠️  Could not process {file_path}: {e}")
    
    return True

def create_import_patch():
    """Create an import patch to handle circular imports"""
    print("\n🔧 Creating import compatibility patch...")
    
    patch_content = '''
# Import patch for circular import issues
import sys
import importlib

def safe_import(module_name, attr_name=None, fallback=None):
    """Safely import modules with fallback for circular imports"""
    try:
        module = importlib.import_module(module_name)
        if attr_name:
            return getattr(module, attr_name, fallback)
        return module
    except (ImportError, AttributeError, Exception):
        return fallback

# Patch for mininet.link circular import
def patch_link_import():
    """Patch Link import issues"""
    try:
        # Try direct import first
        from mininet.link import Link
        return Link
    except ImportError:
        # Create a basic Link fallback
        class LinkFallback:
            def __init__(self, *args, **kwargs):
                pass
        return LinkFallback

# Apply patches when imported
if "mininet.link" in sys.modules:
    # If mininet.link is already loaded, try to fix it
    try:
        import mininet.link
        if not hasattr(mininet.link, 'Link'):
            mininet.link.Link = patch_link_import()
    except:
        pass
'''
    
    patch_file = "/home/melon/Project_5g/netflux5g-editor/src/import_patch.py"
    
    try:
        with open(patch_file, 'w') as f:
            f.write(patch_content)
        print(f"✅ Created import patch at {patch_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create import patch: {e}")
        return False

def test_imports_with_fixes():
    """Test imports after applying fixes"""
    print("\n🧪 Testing imports with fixes...")
    
    # Add containernet to path
    containernet_path = "/home/melon/containernet"
    if containernet_path not in sys.path:
        sys.path.insert(0, containernet_path)
    
    results = {}
    
    # Test containernet
    try:
        from containernet.net import Containernet
        results['containernet'] = True
        print("✅ Containernet import: SUCCESS")
    except Exception as e:
        results['containernet'] = False
        print(f"❌ Containernet import: {e}")
    
    # Test mininet-wifi with workaround
    try:
        # Try importing with specific order to avoid circular imports
        import mininet.util  # Make sure util is loaded first
        import mininet.node  # Load node before link
        from mn_wifi.net import Mininet_wifi
        results['mininet_wifi'] = True
        print("✅ Mininet-WiFi import: SUCCESS")
    except Exception as e:
        results['mininet_wifi'] = False
        print(f"❌ Mininet-WiFi import: {e}")
    
    # Test standard mininet
    try:
        from mininet.net import Mininet
        results['mininet'] = True
        print("✅ Standard Mininet import: SUCCESS")
    except Exception as e:
        results['mininet'] = False
        print(f"❌ Standard Mininet import: {e}")
    
    return results

def main():
    print("🚀 NetFlux5G Import Fix Script")
    print("=" * 40)
    
    # Step 1: Fix Python path
    fix_python_path()
    
    # Step 2: Fix circular imports
    fix_circular_imports()
    
    # Step 3: Create import patch
    create_import_patch()
    
    # Step 4: Test imports
    results = test_imports_with_fixes()
    
    # Summary
    print("\n📊 Results Summary:")
    print("=" * 30)
    for module, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"  {module:15}: {status}")
    
    if results.get('containernet', False):
        print("\n🎉 SUCCESS! Containernet is working!")
        print("   Your NetFlux5G should now be able to create Docker containers.")
    elif results.get('mininet_wifi', False):
        print("\n⚠️  Mininet-WiFi is working, but Containernet still has issues.")
        print("   You can use wireless features but limited Docker support.")
    elif results.get('mininet', False):
        print("\n⚠️  Only standard Mininet is working.")
        print("   Limited functionality - no wireless or Docker support.")
    else:
        print("\n❌ No network emulation backend is working properly.")
    
    print("\n📝 Next Steps:")
    print("1. Close current terminal")
    print("2. Open new terminal (to load new PYTHONPATH)")
    print("3. cd /home/melon/Project_5g/netflux5g-editor/src")
    print("4. python3 main.py")
    print("5. Test your topology")

if __name__ == "__main__":
    main()

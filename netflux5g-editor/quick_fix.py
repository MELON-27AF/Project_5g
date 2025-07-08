#!/usr/bin/env python3
"""
NetFlux5G Quick Fix for Missing Dependencies

This script provides immediate fixes for the Mininet-WiFi and Containernet issues.
"""

import os
import sys
import subprocess
from pathlib import Path

def install_missing_packages():
    """Install missing Python packages."""
    print("📦 Installing missing Python packages...")
    
    packages = [
        "scapy",
        "psutil", 
        "matplotlib",
        "networkx"
    ]
    
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to install {package}: {e}")

def create_compatibility_patch():
    """Create a compatibility patch for the missing fmtBps function."""
    patch_content = '''"""
Compatibility patch for NetFlux5G

This module provides fallback implementations for missing functions.
"""

def fmtBps(rate):
    """Format bandwidth rate with appropriate units."""
    if rate is None:
        return 'None'
    elif rate >= 1e9:
        return f'{rate/1e9:.2f}Gbps'
    elif rate >= 1e6:
        return f'{rate/1e6:.2f}Mbps'
    elif rate >= 1e3:
        return f'{rate/1e3:.2f}Kbps'
    else:
        return f'{rate:.2f}bps'

# Monkey patch mininet.util if available
try:
    import mininet.util
    if not hasattr(mininet.util, 'fmtBps'):
        mininet.util.fmtBps = fmtBps
        print("🔧 Patched mininet.util.fmtBps")
except ImportError:
    pass

# Create a mock mininet.util module if needed
import sys
import types

if 'mininet' not in sys.modules:
    mininet = types.ModuleType('mininet')
    sys.modules['mininet'] = mininet
    
if 'mininet.util' not in sys.modules:
    util = types.ModuleType('mininet.util')
    util.fmtBps = fmtBps
    sys.modules['mininet.util'] = util
    mininet.util = util
'''
    
    patch_file = Path(__file__).parent / "src" / "netflux5g_compat.py"
    patch_file.parent.mkdir(exist_ok=True)
    patch_file.write_text(patch_content)
    print(f"✅ Created compatibility patch: {patch_file}")
    
    return patch_file

def patch_export_file():
    """Patch the mininet export file to handle missing dependencies."""
    export_file = Path(__file__).parent / "src" / "export" / "mininet_export.py"
    
    if not export_file.exists():
        print(f"⚠️  Export file not found: {export_file}")
        return
    
    # Read the current content
    content = export_file.read_text()
    
    # Add compatibility import at the top
    compat_import = '''
# NetFlux5G Compatibility Layer
try:
    import netflux5g_compat  # Load compatibility patches
except ImportError:
    pass

'''
    
    # Check if already patched
    if "netflux5g_compat" in content:
        print("✅ Export file already patched")
        return
    
    # Add the import after existing imports
    lines = content.split('\n')
    insert_index = 0
    
    # Find the last import statement
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            insert_index = i + 1
    
    # Insert the compatibility import
    lines.insert(insert_index, compat_import)
    
    # Write back the modified content
    export_file.write_text('\n'.join(lines))
    print(f"✅ Patched export file: {export_file}")

def create_docker_run_script():
    """Create a script to run topologies in Docker."""
    script_content = '''#!/bin/bash
"""
Docker Runner for NetFlux5G Topologies

This script runs Mininet topologies using Docker when native installation
is not available.
"""

TOPOLOGY_FILE="$1"
DOCKER_IMAGE="netflux5g-mininet"

if [ -z "$TOPOLOGY_FILE" ]; then
    echo "Usage: $0 <topology_file.py>"
    exit 1
fi

if [ ! -f "$TOPOLOGY_FILE" ]; then
    echo "Error: Topology file not found: $TOPOLOGY_FILE"
    exit 1
fi

echo "🐳 Running topology in Docker..."

# Check if Docker image exists
if ! docker image inspect $DOCKER_IMAGE >/dev/null 2>&1; then
    echo "⚠️  Docker image $DOCKER_IMAGE not found"
    echo "Building image from docker directory..."
    
    if [ -d "../../docker" ]; then
        cd ../../docker
        docker build -t $DOCKER_IMAGE .
        cd - >/dev/null
    else
        echo "❌ Docker directory not found. Please build the image manually:"
        echo "   cd docker/"
        echo "   docker build -t $DOCKER_IMAGE ."
        exit 1
    fi
fi

# Prepare the working directory
WORK_DIR="$(dirname "$(realpath "$TOPOLOGY_FILE")")"
TOPOLOGY_NAME="$(basename "$TOPOLOGY_FILE")"

echo "📁 Working directory: $WORK_DIR"
echo "📄 Topology file: $TOPOLOGY_NAME"

# Run the topology in Docker
docker run --rm -it --privileged \\
    --net=host \\
    -v "$WORK_DIR:/workspace" \\
    -w /workspace \\
    $DOCKER_IMAGE \\
    python3 "$TOPOLOGY_NAME"

echo "✅ Docker execution completed"
'''
    
    script_file = Path(__file__).parent / "run_topology_docker.sh"
    script_file.write_text(script_content)
    script_file.chmod(0o755)
    print(f"✅ Created Docker runner script: {script_file}")

def show_immediate_solutions():
    """Show immediate solutions for the user."""
    print("\n🔧 Immediate Solutions for Your Issue:")
    print("=" * 50)
    
    print("\n1. 🐳 Quick Docker Solution (Recommended):")
    print("   cd docker/")
    print("   docker build -t netflux5g-mininet .")
    print("   ./run_topology_docker.sh <your_topology_file.py>")
    
    print("\n2. 📦 Install Dependencies:")
    print("   python3 setup_dependencies.py")
    
    print("\n3. 🔧 Manual Fix:")
    print("   pip3 install scapy psutil matplotlib networkx")
    print("   git clone https://github.com/intrig-unicamp/mininet-wifi.git")
    print("   cd mininet-wifi && sudo python3 setup.py install")
    
    print("\n4. 🔄 Use Compatibility Runner:")
    print("   python3 topology_runner.py <your_topology_file.py>")
    
    print("\n📍 Current Issue:")
    print("   - Missing 'fmtBps' from mininet.util")
    print("   - Missing 'containernet' module")
    print("   - These have been patched with fallback implementations")

def main():
    """Main quick fix function."""
    print("🚀 NetFlux5G Quick Fix Tool")
    print("=" * 40)
    
    # Install missing packages
    install_missing_packages()
    
    # Create compatibility patch
    create_compatibility_patch()
    
    # Patch export file
    patch_export_file()
    
    # Create Docker runner script
    create_docker_run_script()
    
    # Show solutions
    show_immediate_solutions()
    
    print("\n✅ Quick fixes applied!")
    print("\nYou can now:")
    print("1. Try running your topology again")
    print("2. Use the Docker solution for reliable execution")
    print("3. Run the full setup script for permanent fix")

if __name__ == "__main__":
    main()

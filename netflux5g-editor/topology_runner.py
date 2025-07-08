#!/usr/bin/env python3
"""
NetFlux5G Topology Runner with Fallback Support

This script provides intelligent fallback mechanisms for running Mininet topologies
when specific dependencies are not available.
"""

import sys
import os
import importlib.util
import subprocess
import traceback
from pathlib import Path

class DependencyManager:
    """Manages network emulation dependencies and provides fallbacks."""
    
    def __init__(self):
        self.available_backends = []
        self.selected_backend = None
        self.check_dependencies()
    
    def check_import(self, module_name, package_name=None):
        """Check if a module can be imported."""
        try:
            if package_name:
                spec = importlib.util.find_spec(f"{package_name}.{module_name}")
            else:
                spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, AttributeError):
            return False
    
    def check_dependencies(self):
        """Check available network emulation backends."""
        print("🔍 Checking available network emulation backends...")
        
        # Check for Mininet-WiFi
        if self.check_import("net", "mn_wifi") and self.check_import("cli", "mn_wifi"):
            try:
                # Additional check for the problematic fmtBps function
                from mininet.util import fmtBps
                self.available_backends.append({
                    'name': 'mininet-wifi',
                    'priority': 1,
                    'description': 'Mininet-WiFi (full wireless support)',
                    'net_class': 'mn_wifi.net.Mininet_wifi',
                    'cli_class': 'mn_wifi.cli.CLI'
                })
                print("✅ Mininet-WiFi detected (with fmtBps support)")
            except ImportError as e:
                print(f"⚠️  Mininet-WiFi detected but missing fmtBps: {e}")
                # Try to use it anyway with a warning
                self.available_backends.append({
                    'name': 'mininet-wifi-limited',
                    'priority': 3,
                    'description': 'Mininet-WiFi (limited, missing fmtBps)',
                    'net_class': 'mn_wifi.net.Mininet_wifi',
                    'cli_class': 'mn_wifi.cli.CLI',
                    'warning': 'Missing fmtBps function - some features may not work'
                })
        
        # Check for Containernet
        if self.check_import("net", "containernet") and self.check_import("cli", "containernet"):
            self.available_backends.append({
                'name': 'containernet',
                'priority': 2,
                'description': 'Containernet (Docker container support)',
                'net_class': 'containernet.net.Containernet',
                'cli_class': 'containernet.cli.CLI'
            })
            print("✅ Containernet detected")
        
        # Check for standard Mininet
        if self.check_import("net", "mininet") and self.check_import("cli", "mininet"):
            self.available_backends.append({
                'name': 'mininet',
                'priority': 4,
                'description': 'Standard Mininet (basic support)',
                'net_class': 'mininet.net.Mininet',
                'cli_class': 'mininet.cli.CLI'
            })
            print("✅ Standard Mininet detected")
        
        # Sort by priority
        self.available_backends.sort(key=lambda x: x['priority'])
        
        if not self.available_backends:
            print("❌ No compatible network emulation backend found!")
            return False
        
        # Select the best available backend
        self.selected_backend = self.available_backends[0]
        print(f"🎯 Selected backend: {self.selected_backend['description']}")
        
        if 'warning' in self.selected_backend:
            print(f"⚠️  Warning: {self.selected_backend['warning']}")
        
        return True
    
    def get_backend_classes(self):
        """Get the network and CLI classes for the selected backend."""
        if not self.selected_backend:
            raise RuntimeError("No backend available")
        
        # Import the classes dynamically
        net_module, net_class = self.selected_backend['net_class'].rsplit('.', 1)
        cli_module, cli_class = self.selected_backend['cli_class'].rsplit('.', 1)
        
        net_mod = importlib.import_module(net_module)
        cli_mod = importlib.import_module(cli_module)
        
        return getattr(net_mod, net_class), getattr(cli_mod, cli_class)
    
    def create_patched_imports(self):
        """Create patched imports for missing functions."""
        if self.selected_backend['name'] == 'mininet-wifi-limited':
            # Patch the missing fmtBps function
            try:
                from mininet import util
                if not hasattr(util, 'fmtBps'):
                    def fmtBps(rate):
                        """Fallback implementation of fmtBps."""
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
                    
                    # Monkey patch the function
                    util.fmtBps = fmtBps
                    print("🔧 Patched missing fmtBps function")
            except Exception as e:
                print(f"⚠️  Could not patch fmtBps: {e}")

def run_docker_fallback(topology_file):
    """Run topology using Docker as a fallback."""
    print("\n🐳 Attempting to run using Docker fallback...")
    
    # Check if Docker is available
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not available")
        return False
    
    # Look for the netflux5g Docker image
    docker_images = ['netflux5g-mininet', 'netflux5g:latest', 'containernet/containernet']
    
    for image in docker_images:
        try:
            # Check if image exists
            subprocess.run(['docker', 'image', 'inspect', image], 
                         check=True, capture_output=True)
            
            print(f"🎯 Using Docker image: {image}")
            
            # Mount the topology file and run it
            cmd = [
                'docker', 'run', '--rm', '-it', '--privileged',
                '--net=host',
                '-v', f'{os.path.dirname(os.path.abspath(topology_file))}:/workspace',
                image,
                'python3', f'/workspace/{os.path.basename(topology_file)}'
            ]
            
            print(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd)
            return True
            
        except subprocess.CalledProcessError:
            continue
    
    print("❌ No suitable Docker image found")
    print("Build the NetFlux5G Docker image with: docker build -t netflux5g-mininet .")
    return False

def show_installation_help():
    """Show installation instructions."""
    print("\n📚 Installation Help")
    print("=" * 50)
    print("\n🔧 Quick Setup:")
    print("   python3 setup_dependencies.py")
    print("\n🐳 Docker Alternative:")
    print("   cd docker/")
    print("   docker build -t netflux5g-mininet .")
    print("\n📦 Manual Installation:")
    print("   # Mininet-WiFi")
    print("   git clone https://github.com/intrig-unicamp/mininet-wifi.git")
    print("   cd mininet-wifi")
    print("   sudo python3 setup.py install")
    print("\n   # Containernet")
    print("   git clone https://github.com/containernet/containernet.git")
    print("   cd containernet")
    print("   sudo python3 setup.py install")
    print("\n💡 For more help, see: README.md")

def main():
    """Main function."""
    print("🚀 NetFlux5G Topology Runner")
    print("=" * 40)
    
    # Check if topology file is provided
    if len(sys.argv) < 2:
        print("❌ No topology file provided")
        print("Usage: python3 topology_runner.py <topology_file.py>")
        sys.exit(1)
    
    topology_file = sys.argv[1]
    
    if not os.path.exists(topology_file):
        print(f"❌ Topology file not found: {topology_file}")
        sys.exit(1)
    
    print(f"📄 Loading topology: {topology_file}")
    
    # Initialize dependency manager
    dep_manager = DependencyManager()
    
    if not dep_manager.available_backends:
        print("\n❌ No network emulation backends available!")
        print("\nTrying Docker fallback...")
        
        if not run_docker_fallback(topology_file):
            show_installation_help()
            sys.exit(1)
        return
    
    try:
        # Apply patches if needed
        dep_manager.create_patched_imports()
        
        # Get backend classes
        Net, CLI = dep_manager.get_backend_classes()
        
        print(f"🎯 Using: {dep_manager.selected_backend['description']}")
        
        # Execute the topology file with the selected backend
        print("🚀 Starting topology...")
        
        # Set up the environment for the topology script
        globals_dict = {
            '__file__': topology_file,
            '__name__': '__main__',
            'Net': Net,
            'CLI': CLI,
            # Add common imports that topologies might need
            'sys': sys,
            'os': os,
        }
        
        # Try to import and add other common modules
        common_modules = [
            'mininet.node', 'mininet.link', 'mininet.log',
            'mn_wifi.node', 'mn_wifi.link', 'containernet.node'
        ]
        
        for module_name in common_modules:
            try:
                module = importlib.import_module(module_name)
                globals_dict[module_name.split('.')[-1]] = module
            except ImportError:
                pass
        
        # Execute the topology file
        with open(topology_file, 'r') as f:
            topology_code = f.read()
        
        exec(topology_code, globals_dict)
        
    except Exception as e:
        print(f"\n❌ Error running topology: {e}")
        traceback.print_exc()
        
        print("\n🐳 Trying Docker fallback...")
        if not run_docker_fallback(topology_file):
            show_installation_help()
            sys.exit(1)

if __name__ == "__main__":
    main()

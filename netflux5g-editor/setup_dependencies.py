#!/usr/bin/env python3
"""
NetFlux5G Dependencies Setup Script

This script helps set up the required dependencies for NetFlux5G,
including Mininet-WiFi and Containernet for network emulation.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description, ignore_errors=False):
    """Run a command and display progress."""
    print(f"\n🔄 {description}...")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print(f"⚠️  {description} failed (ignored): {e}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            return False
        else:
            print(f"❌ {description} failed: {e}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            sys.exit(1)

def check_system():
    """Check system requirements."""
    print("🔍 Checking system requirements...")
    
    # Check if running on Linux
    if platform.system() != 'Linux':
        print("⚠️  Warning: Mininet-WiFi and Containernet work best on Linux systems.")
        print("   Consider using Docker or WSL2 on Windows/macOS.")
    
    # Check if running as root/sudo
    if os.geteuid() == 0:
        print("✅ Running with root privileges")
    else:
        print("⚠️  Note: Some operations may require sudo privileges")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 7):
        print(f"✅ Python {python_version.major}.{python_version.minor} detected")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} detected. Python 3.7+ required.")
        sys.exit(1)

def install_python_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    
    # Basic requirements
    requirements = [
        "PyQt5",
        "PyYAML",
        "docker",
        "requests",
        "matplotlib",
        "networkx"
    ]
    
    for package in requirements:
        run_command(f"pip3 install {package}", f"Installing {package}")

def setup_mininet_wifi():
    """Set up Mininet-WiFi."""
    print("\n🌐 Setting up Mininet-WiFi...")
    
    # Check if already installed
    try:
        import mn_wifi
        print("✅ Mininet-WiFi already installed")
        return
    except ImportError:
        pass
    
    # Clone and install Mininet-WiFi
    wifi_dir = Path.home() / "mininet-wifi"
    
    if not wifi_dir.exists():
        run_command(
            f"git clone https://github.com/intrig-unicamp/mininet-wifi.git {wifi_dir}",
            "Cloning Mininet-WiFi repository"
        )
    
    # Install dependencies
    run_command(
        "apt-get update && apt-get install -y git make gcc python3-dev python3-setuptools",
        "Installing system dependencies",
        ignore_errors=True
    )
    
    # Install Mininet-WiFi
    os.chdir(wifi_dir)
    run_command("sudo python3 setup.py install", "Installing Mininet-WiFi")

def setup_containernet():
    """Set up Containernet."""
    print("\n🐳 Setting up Containernet...")
    
    # Check if already installed
    try:
        import containernet
        print("✅ Containernet already installed")
        return
    except ImportError:
        pass
    
    # Clone and install Containernet
    containernet_dir = Path.home() / "containernet"
    
    if not containernet_dir.exists():
        run_command(
            f"git clone https://github.com/containernet/containernet.git {containernet_dir}",
            "Cloning Containernet repository"
        )
    
    # Install Containernet
    os.chdir(containernet_dir)
    run_command("sudo python3 setup.py install", "Installing Containernet")

def setup_docker_alternative():
    """Set up Docker-based solution as an alternative."""
    print("\n🐳 Setting up Docker-based Mininet environment...")
    
    docker_dir = Path(__file__).parent.parent / "docker"
    os.chdir(docker_dir)
    
    # Build Docker image
    run_command(
        "docker build -t netflux5g-mininet .",
        "Building NetFlux5G Mininet Docker image"
    )
    
    print("\n✅ Docker image built successfully!")
    print("You can now run Mininet topologies using:")
    print("docker run --privileged --rm -it netflux5g-mininet")

def create_wrapper_scripts():
    """Create wrapper scripts for easier usage."""
    print("\n📝 Creating wrapper scripts...")
    
    scripts_dir = Path(__file__).parent / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    # Create mininet wrapper script
    mininet_wrapper = scripts_dir / "run_mininet.py"
    mininet_wrapper.write_text('''#!/usr/bin/env python3
"""
Mininet Wrapper Script for NetFlux5G

This script provides fallback mechanisms for running Mininet topologies
when Mininet-WiFi or Containernet are not available.
"""

import sys
import importlib.util

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        if package_name:
            spec = importlib.util.find_spec(f"{package_name}.{module_name}")
        else:
            spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ImportError:
        return False

def main():
    """Main wrapper function."""
    print("NetFlux5G Mininet Wrapper")
    print("=" * 30)
    
    # Check for Mininet-WiFi
    if check_import("net", "mn_wifi"):
        print("✅ Mininet-WiFi detected")
        from mn_wifi.net import Mininet_wifi as Net
        from mn_wifi.cli import CLI
    elif check_import("cli", "containernet"):
        print("✅ Containernet detected")
        from containernet.net import Containernet as Net
        from containernet.cli import CLI
    elif check_import("net", "mininet"):
        print("⚠️  Using standard Mininet (limited wireless support)")
        from mininet.net import Mininet as Net
        from mininet.cli import CLI
    else:
        print("❌ No Mininet installation found!")
        print("Please install Mininet-WiFi, Containernet, or standard Mininet.")
        sys.exit(1)
    
    print(f"Using: {Net.__module__}")
    
    # Run the topology script if provided
    if len(sys.argv) > 1:
        topology_script = sys.argv[1]
        print(f"Running topology: {topology_script}")
        exec(open(topology_script).read())
    else:
        print("No topology script provided")
        print("Usage: python3 run_mininet.py <topology_script.py>")

if __name__ == "__main__":
    main()
''')
    
    mininet_wrapper.chmod(0o755)
    print(f"✅ Created wrapper script: {mininet_wrapper}")

def main():
    """Main setup function."""
    print("🚀 NetFlux5G Dependencies Setup")
    print("=" * 40)
    
    # Check system
    check_system()
    
    # Install Python dependencies
    install_python_dependencies()
    
    # Check if user wants Docker or native installation
    if platform.system() == 'Linux':
        choice = input("\nChoose installation method:\n"
                      "1. Native installation (Mininet-WiFi + Containernet)\n"
                      "2. Docker-based solution (recommended)\n"
                      "3. Both\n"
                      "Enter choice (1/2/3): ").strip()
        
        if choice in ['1', '3']:
            try:
                setup_mininet_wifi()
                setup_containernet()
            except Exception as e:
                print(f"❌ Native installation failed: {e}")
                print("Falling back to Docker solution...")
                setup_docker_alternative()
        
        if choice in ['2', '3']:
            setup_docker_alternative()
    else:
        print("Non-Linux system detected. Setting up Docker solution...")
        setup_docker_alternative()
    
    # Create wrapper scripts
    create_wrapper_scripts()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. For Docker: Use the Docker commands shown above")
    print("2. For native: Test with 'python3 -c \"import mn_wifi; print('Success!')\"'")
    print("3. Run NetFlux5G: python3 src/main.py")

if __name__ == "__main__":
    main()

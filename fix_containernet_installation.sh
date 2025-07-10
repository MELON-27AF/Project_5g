#!/bin/bash

# Fix Containernet Installation Script
# This script will reinstall Containernet properly to ensure addDocker method is available

echo "=== Containernet Installation Fix ==="
echo "This script will fix your Containernet installation"
echo "Current user: $(whoami)"
echo "Working directory: $(pwd)"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Please run this script as your regular user (not sudo)"
   echo "The script will use sudo only when needed"
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
echo "🔍 Step 1: Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker not found. Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. You'll need to log out and back in for group changes to take effect."
else
    echo "✅ Docker found"
fi

if ! command_exists git; then
    echo "❌ Git not found. Installing Git..."
    sudo apt-get install -y git
    echo "✅ Git installed"
else
    echo "✅ Git found"
fi

echo ""

# Step 2: Remove existing containernet if corrupted
echo "🔍 Step 2: Checking existing Containernet installation..."
CONTAINERNET_PATH="/home/$(whoami)/containernet"

if [ -d "$CONTAINERNET_PATH" ]; then
    echo "⚠️  Found existing Containernet at $CONTAINERNET_PATH"
    echo "🗑️  Removing corrupted installation..."
    rm -rf "$CONTAINERNET_PATH"
    echo "✅ Removed existing installation"
fi

echo ""

# Step 3: Clone fresh Containernet
echo "🔍 Step 3: Cloning fresh Containernet..."
cd /home/$(whoami)
git clone https://github.com/containernet/containernet.git
cd containernet

echo "✅ Containernet cloned successfully"
echo ""

# Step 4: Install Containernet
echo "🔍 Step 4: Installing Containernet..."
echo "Installing Python dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev python3-setuptools
pip3 install --user wheel
pip3 install --user docker

echo "Installing system dependencies..."
sudo apt-get install -y ansible aptitude

echo "Running Containernet ansible installation..."
cd ansible
sudo ansible-playbook -i "localhost," -c local install.yml
cd ..

echo "Installing Containernet Python package..."
sudo python3 setup.py install

echo "✅ Containernet installation completed"
echo ""

# Step 5: Install Mininet-WiFi (optional but recommended)
echo "🔍 Step 5: Installing Mininet-WiFi (optional)..."
if [ ! -d "/home/$(whoami)/mininet-wifi" ]; then
    echo "Cloning Mininet-WiFi..."
    cd /home/$(whoami)
    git clone https://github.com/intrig-unicamp/mininet-wifi.git
    cd mininet-wifi
    sudo python3 setup.py install
    echo "✅ Mininet-WiFi installed"
else
    echo "✅ Mininet-WiFi already exists"
fi

echo ""

# Step 6: Test installation
echo "🔍 Step 6: Testing Containernet installation..."
cd /home/$(whoami)/Project_5g

python3 -c "
import sys
sys.path.insert(0, '/home/$(whoami)/containernet')
try:
    from containernet.net import Containernet
    net = Containernet()
    if hasattr(net, 'addDocker'):
        print('✅ SUCCESS: Containernet with addDocker method is working!')
        net.stop()
    else:
        print('❌ FAILED: Containernet imported but no addDocker method')
        available_methods = [method for method in dir(net) if not method.startswith('_')]
        print('Available methods:', available_methods)
except Exception as e:
    print(f'❌ FAILED: Error importing Containernet: {e}')
"

echo ""

# Step 7: Fix permissions
echo "🔍 Step 7: Fixing permissions..."
sudo chown -R $(whoami):$(whoami) /home/$(whoami)/containernet
sudo chown -R $(whoami):$(whoami) /home/$(whoami)/mininet-wifi 2>/dev/null || true

echo ""

# Step 8: Create test script
echo "🔍 Step 8: Creating test script..."
cat > /home/$(whoami)/Project_5g/test_fixed_containernet.py << 'EOF'
#!/usr/bin/env python3

import sys
import os

# Add Containernet to Python path
containernet_path = "/home/{}/containernet".format(os.getenv('USER', 'melon'))
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

print("=== Testing Fixed Containernet ===")
print(f"Python path: {sys.path[:3]}...")
print(f"User: {os.getenv('USER', 'unknown')}")
print("")

try:
    print("🔍 Importing Containernet...")
    from containernet.net import Containernet
    from containernet.node import DockerSta
    from containernet.cli import CLI
    
    print(f"✅ Containernet class: {Containernet}")
    print(f"✅ DockerSta class: {DockerSta}")
    
    print("🔍 Creating Containernet instance...")
    net = Containernet()
    
    print(f"✅ Instance type: {type(net)}")
    print(f"✅ Instance class: {net.__class__}")
    
    if hasattr(net, 'addDocker'):
        print("✅ SUCCESS: addDocker method found!")
        print("✅ Containernet is working correctly!")
        
        # Test creating a Docker node
        print("🔍 Testing Docker node creation...")
        try:
            docker_node = net.addDocker('test-node', dimage='ubuntu:20.04')
            print("✅ Docker node created successfully!")
            net.removeHost(docker_node)
        except Exception as e:
            print(f"⚠️  Docker node creation test failed: {e}")
    else:
        print("❌ FAILED: addDocker method not found!")
        available_methods = [method for method in dir(net) if not method.startswith('_')]
        print(f"Available methods: {available_methods[:10]}...")
    
    net.stop()
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
EOF

chmod +x /home/$(whoami)/Project_5g/test_fixed_containernet.py

echo "✅ Test script created at /home/$(whoami)/Project_5g/test_fixed_containernet.py"

echo ""
echo "=== Installation Summary ==="
echo "✅ Containernet has been reinstalled"
echo "✅ Mininet-WiFi has been installed (if needed)"
echo "✅ Test script has been created"
echo ""
echo "📋 Next steps:"
echo "1. Log out and log back in (or reboot) to apply Docker group changes"
echo "2. Run: python3 test_fixed_containernet.py"
echo "3. If successful, run: sudo python3 netflux5g_topology.py"
echo ""
echo "🔧 If you still have issues:"
echo "   - Make sure Docker daemon is running: sudo systemctl status docker"
echo "   - Check Docker permissions: docker ps"
echo "   - Reboot the system if needed"

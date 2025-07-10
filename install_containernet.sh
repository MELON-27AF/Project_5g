#!/bin/bash
# Containernet Installation/Fix Script for Ubuntu/VirtualBox

echo "🚀 Containernet Installation/Fix Script"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update

# Install required dependencies
echo "📦 Installing dependencies..."
apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-dev \
    docker.io \
    docker-compose \
    build-essential \
    pkg-config \
    libc6-dev \
    libffi-dev \
    libssl-dev

# Enable and start Docker
echo "🐳 Setting up Docker..."
systemctl enable docker
systemctl start docker

# Add current user to docker group
if [ -n "$SUDO_USER" ]; then
    usermod -aG docker $SUDO_USER
    echo "✅ Added $SUDO_USER to docker group"
fi

# Check if Containernet directory exists
CONTAINERNET_DIR="/home/melon/containernet"
if [ -d "$CONTAINERNET_DIR" ]; then
    echo "📁 Containernet directory exists, backing up..."
    mv "$CONTAINERNET_DIR" "${CONTAINERNET_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

# Clone Containernet
echo "📥 Cloning Containernet..."
cd /home/melon
git clone https://github.com/containernet/containernet.git
cd containernet

# Install Containernet
echo "🔧 Installing Containernet..."
python3 util/install.py -W

# Install additional Python packages
echo "📦 Installing Python packages..."
pip3 install docker

# Fix permissions
echo "🔧 Fixing permissions..."
chown -R melon:melon /home/melon/containernet

# Test installation
echo "🧪 Testing Containernet installation..."
cd /home/melon/containernet
python3 -c "
try:
    from containernet.net import Containernet
    print('✅ Containernet import successful')
    net = Containernet()
    if hasattr(net, 'addDocker'):
        print('✅ addDocker method available')
    else:
        print('❌ addDocker method not available')
    net.stop()
    print('✅ Containernet test completed successfully')
except Exception as e:
    print(f'❌ Containernet test failed: {e}')
"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Logout and login again (or reboot) to apply docker group changes"
echo "2. Test with: cd /home/melon/Project_5g && sudo python3 debug_containernet.py"
echo "3. Run your topology: cd /home/melon/Project_5g && sudo python3 netflux5g_topology.py"

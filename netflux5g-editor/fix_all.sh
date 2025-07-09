#!/bin/bash
# NetFlux5G Docker Container Fix Script
# This script fixes the container startup issues

echo "🚀 NetFlux5G Container Fix Script"
echo "=================================="

# Step 1: Fix the fmtBps function in mininet.util
echo "🔧 Step 1: Fixing fmtBps function..."
python3 fix_fmtbps.py

# Step 2: Test current imports
echo -e "\n🧪 Step 2: Testing current imports..."
python3 -c "
try:
    from containernet.net import Containernet
    print('✅ Containernet import: OK')
except ImportError as e:
    print(f'❌ Containernet import: {e}')

try:
    from mn_wifi.net import Mininet_wifi
    print('✅ Mininet-WiFi import: OK')
except ImportError as e:
    print(f'❌ Mininet-WiFi import: {e}')

try:
    import mininet.util
    if hasattr(mininet.util, 'fmtBps'):
        print('✅ fmtBps function: OK')
    else:
        print('❌ fmtBps function: Missing')
except ImportError as e:
    print(f'❌ mininet.util import: {e}')
"

# Step 3: Check Docker setup
echo -e "\n🐳 Step 3: Checking Docker setup..."
docker --version
echo "Docker networks:"
docker network ls | grep -E "(open5gs|netflux5g)"

echo "Docker images for 5G:"
docker images | grep -E "(adaptive|open5gs|ueransim)"

# Step 4: Instructions
echo -e "\n📋 Step 4: Instructions to test the fix"
echo "========================================"
echo "1. Open NetFlux5G GUI:"
echo "   cd /home/melon/Project_5g/netflux5g-editor/src"
echo "   python3 main.py"
echo ""
echo "2. Load a topology with 5G components"
echo ""
echo "3. Click 'Run All' from the toolbar"
echo ""
echo "4. Check if containers are created:"
echo "   docker ps -a"
echo ""
echo "5. If containers are created, the fix worked! 🎉"
echo ""
echo "💡 If you still have issues:"
echo "   - Restart your terminal"
echo "   - Run: source ~/.bashrc"
echo "   - Try running the topology again"

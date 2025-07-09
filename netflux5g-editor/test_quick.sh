#!/bin/bash
# Quick test to see if the export fixes work

echo "🚀 Testing NetFlux5G Export Fix"
echo "==============================="

echo "1. Testing topology export from GUI..."
cd /home/melon/Project_5g/netflux5g-editor/src

# Check if we can import required modules
echo "2. Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, '/home/melon/containernet')

try:
    from containernet.net import Containernet
    from containernet.node import DockerSta
    print('✅ Containernet imports: OK')
except ImportError as e:
    print(f'❌ Containernet imports: {e}')

try:
    import mininet.util
    if hasattr(mininet.util, 'fmtBps'):
        print('✅ fmtBps function: OK')
    else:
        print('❌ fmtBps function: Missing')
except ImportError as e:
    print(f'❌ mininet.util: {e}')

try:
    import mininet.node
    from mn_wifi.net import Mininet_wifi
    print('✅ Mininet-WiFi imports: OK')
except ImportError as e:
    print(f'❌ Mininet-WiFi imports: {e}')
"

echo ""
echo "3. Instructions to test the full fix:"
echo "   a. Open NetFlux5G GUI: python3 main.py"
echo "   b. Load a topology with 5G components (UE, gNB, VGCore)"
echo "   c. Click 'Run All'"
echo "   d. Check output should show:"
echo "      '✓ containernet available - using Docker support'"
echo "      'Using Containernet for Docker container support'"
echo "   e. Verify containers: docker ps -a"
echo ""
echo "💡 If you see error, export the topology again after our fixes"

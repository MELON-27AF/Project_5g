#!/usr/bin/env python3
"""
Direct Containernet Test
This script tests Containernet directly to see what's going wrong
"""

import sys
import os

# Add containernet to path
containernet_path = "/home/melon/containernet"
if containernet_path not in sys.path:
    sys.path.insert(0, containernet_path)

print("=== Direct Containernet Test ===")
print(f"Python path includes: {containernet_path}")

try:
    # Import containernet directly
    print("\n🔍 Step 1: Import containernet module")
    import containernet
    print(f"✅ containernet module location: {containernet.__file__}")
    
    print("\n🔍 Step 2: Import Containernet class")
    from containernet.net import Containernet
    print(f"✅ Containernet class: {Containernet}")
    print(f"✅ Containernet class type: {type(Containernet)}")
    print(f"✅ Containernet MRO: {Containernet.__mro__}")
    
    print("\n🔍 Step 3: Create Containernet instance")
    net = Containernet()
    print(f"✅ Created instance: {net}")
    print(f"✅ Instance type: {type(net)}")
    print(f"✅ Instance class: {net.__class__}")
    
    print("\n🔍 Step 4: Check for addDocker method")
    if hasattr(net, 'addDocker'):
        print("✅ addDocker method found!")
        print(f"✅ addDocker method: {net.addDocker}")
        
        # Try to call addDocker (this should work)
        print("\n🔍 Step 5: Test addDocker method")
        try:
            docker_node = net.addDocker('test_container', dimage='alpine:latest')
            print(f"✅ addDocker works! Created: {docker_node}")
            print(f"✅ Docker node type: {type(docker_node)}")
        except Exception as e:
            print(f"❌ addDocker failed: {e}")
            
    else:
        print("❌ addDocker method NOT found!")
        print("Available methods:")
        methods = [method for method in dir(net) if not method.startswith('_')]
        for method in sorted(methods):
            print(f"  - {method}")
    
    print("\n🔍 Step 6: Compare with standard Mininet")
    from mininet.net import Mininet as StandardMininet
    std_net = StandardMininet()
    print(f"Standard Mininet type: {type(std_net)}")
    print(f"Containernet type: {type(net)}")
    print(f"Are they the same? {type(net) == type(std_net)}")
    
    # Cleanup
    net.stop()
    std_net.stop()
    
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()

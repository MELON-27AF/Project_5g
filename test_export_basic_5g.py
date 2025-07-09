#!/usr/bin/env python3
"""
Test script to export the basic 5G topology example with complete 5G core
"""

import sys
import os
import json

# Mock GUI components needed for export
class MockDockerNetworkManager:
    def get_current_network_name(self):
        return "basic_5g_netflux5g_topology"

class MockMainWindow:
    def __init__(self, topology_file):
        self.current_file = topology_file
        self.docker_network_manager = MockDockerNetworkManager()
    
    def extractTopology(self):
        # Load the actual topology file
        with open(self.current_file, 'r') as f:
            topology_data = json.load(f)
        
        nodes = topology_data.get('nodes', [])
        links = topology_data.get('links', [])
        
        print(f"Loaded topology with {len(nodes)} nodes and {len(links)} links")
        
        return nodes, links
    
    def showCanvasStatus(self, message):
        print(f"Status: {message}")

def test_export_basic_5g():
    # Add the netflux5g source to path
    sys.path.insert(0, '/home/melon/Project_5g/netflux5g-editor/src')
    
    try:
        from export.mininet_export import MininetExporter
        
        # Use the basic 5G topology example
        topology_file = "/home/melon/Project_5g/netflux5g-editor/src/examples/basic_5g_topology.nf5g"
        
        if not os.path.exists(topology_file):
            print(f"✗ Topology file not found: {topology_file}")
            return False
        
        # Create mock main window with the topology file
        main_window = MockMainWindow(topology_file)
        
        # Create exporter
        exporter = MininetExporter(main_window)
        
        # Export to test script
        test_script_path = "/home/melon/Project_5g/basic_5g_exported_topology.py"
        exporter.export_to_mininet_script(test_script_path)
        
        print(f"✓ Successfully exported basic 5G topology to: {test_script_path}")
        print("Now run with: sudo python3 basic_5g_exported_topology.py")
        
        return True
        
    except Exception as e:
        print(f"✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_export_basic_5g()

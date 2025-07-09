#!/usr/bin/env python3
"""
Test script to verify that exported topologies use Containernet properly
"""

# Mock GUI components needed for export
class MockDockerNetworkManager:
    def get_current_network_name(self):
        return "test_netflux5g_topology"

class MockMainWindow:
    def __init__(self):
        self.current_file = "/home/melon/test_topology.nf5g"
        self.docker_network_manager = MockDockerNetworkManager()
    
    def extractTopology(self):
        # Create a simple test topology with UE and gNB
        nodes = [
            {
                'name': 'ue1',
                'type': 'UE',
                'x': 100,
                'y': 100,
                'properties': {
                    'UE_IMSI': '001010123456780',
                    'UE_Key': '465B5CE8B199B49FAA5F0A2EE238A6BC',
                    'UE_OP': 'E8ED289DEBA952E4283B54E88E6183CA'
                }
            },
            {
                'name': 'gnb1', 
                'type': 'GNB',
                'x': 200,
                'y': 100,
                'properties': {
                    'GNB_ID': '1',
                    'GNB_TAC': '1',
                    'GNB_PLMN': '00101'
                }
            },
            {
                'name': 'vgcore1',
                'type': 'VGcore',
                'x': 300,
                'y': 100,
                'properties': {
                    'enabled_components': ['NRF', 'AMF', 'SMF', 'UPF', 'UDM', 'UDR', 'PCF', 'AUSF', 'NSSF', 'BSF', 'SCP']
                }
            }
        ]
        
        links = []  # No explicit links - should create default switch
        
        return nodes, links
    
    def showCanvasStatus(self, message):
        print(f"Status: {message}")

def test_export():
    import sys
    import os
    
    # Add the netflux5g source to path
    sys.path.insert(0, '/home/melon/Project_5g/netflux5g-editor/src')
    
    try:
        from export.mininet_export import MininetExporter
        
        # Create mock main window
        main_window = MockMainWindow()
        
        # Create exporter
        exporter = MininetExporter(main_window)
        
        # Export to test script
        test_script_path = "/home/melon/Project_5g/test_exported_topology.py"
        exporter.export_to_mininet_script(test_script_path)
        
        print(f"✓ Successfully exported test topology to: {test_script_path}")
        print("Now run with: sudo python3 test_exported_topology.py")
        
        return True
        
    except Exception as e:
        print(f"✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_export()

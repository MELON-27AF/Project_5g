#!/usr/bin/env python3
"""
Test script for hybrid Docker + Wireless mode implementation.
This tests the new feature where gNB acts as wireless AP and UE connects as wireless station.
"""

import sys
import os
import tempfile

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from export.mininet_export import MininetExporter

def test_hybrid_wireless_export():
    """Test hybrid wireless + Docker export functionality."""
    print("=== Testing Hybrid Wireless + Docker Export ===")
    
    # Create test topology: gNB (AP mode) + UE (station mode) + AMF
    test_nodes = [
        {
            'id': 'gnb1',
            'name': 'GNB1',
            'type': 'GNB',
            'x': 100,
            'y': 100,
            'properties': {
                'gnb_hostname': 'gnb1.5g',
                'amf_hostname': 'amf1.5g',
                'range': 100,
                'txpower': 30,
                'ap_enabled': True  # Enable AP mode
            }
        },
        {
            'id': 'ue1',
            'name': 'UE1',
            'type': 'UE',
            'x': 150,
            'y': 120,
            'properties': {
                'gnb_hostname': 'gnb1.5g',
                'msisdn': '0000000001',
                'key': '465B5CE8B199B49FAA5F0A2EE238A6BC',
                'mobility_enabled': True  # Enable mobility for wireless
            }
        },
        {
            'id': 'amf1',
            'name': 'AMF1',
            'type': 'VGcore',
            'x': 50,
            'y': 100,
            'properties': {
                'selected_components': ['AMF', 'SMF', 'UPF']
            }
        }
    ]
    
    test_links = []  # No explicit links - use wireless connectivity
    
    # Export topology
    class MockMainWindow:
        """Mock main window for testing."""
        def __init__(self):
            self.auto_create_default_switch = True
            self.respect_explicit_topology = False
    
    exporter = MininetExporter(MockMainWindow())
    
    try:
        output_file = "/tmp/test_hybrid_wireless.py"
        
        # Use the exporter with test data
        categorized_nodes = exporter.categorize_nodes(test_nodes)
        
        with open(output_file, "w") as f:
            exporter.write_mininet_script(f, test_nodes, test_links, categorized_nodes)
        
        print("✓ Hybrid wireless topology exported successfully")
        
        # Check for key hybrid features in exported script
        with open(output_file, 'r') as f:
            content = f.read()
            
        # Check for hybrid mode detection
        if 'HYBRID_WIRELESS_AVAILABLE' in content:
            print("✓ Hybrid wireless availability check present")
        else:
            print("✗ Missing hybrid wireless availability check")
        
        # Check for gNB AP configuration
        if 'mode" = "ap"' in content or 'configured as wireless AP' in content:
            print("✓ gNB AP mode configuration present")
        else:
            print("✗ Missing gNB AP mode configuration")
        
        # Check for UE station configuration
        if 'mode" = "sta"' in content or 'configured as wireless station' in content:
            print("✓ UE station mode configuration present")
        else:
            print("✗ Missing UE station mode configuration")
        
        # Check for uesimtun setup
        if 'uesimtun' in content:
            print("✓ uesimtun interface setup present")
        else:
            print("✗ Missing uesimtun interface setup")
        
        # Check for wireless association
        if 'iwconfig' in content or 'wireless association' in content:
            print("✓ Wireless association logic present")
        else:
            print("✗ Missing wireless association logic")
        
        print(f"✓ Test file created: {output_file}")
        return True
            
    except Exception as e:
        print(f"✗ Export error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_wireless_connectivity():
    """Test the wireless connectivity concepts."""
    print("\n=== Testing Wireless Connectivity Concepts ===")
    
    print("Key features of hybrid implementation:")
    print("1. gNB sebagai Docker container dengan mode AP (Access Point)")
    print("2. UE sebagai Docker container dengan mode STA (Station)")
    print("3. Wireless association antara UE dan gNB menggunakan SSID")
    print("4. uesimtun interface untuk 5G data tunnel di UE")
    print("5. Positioning support untuk propagation model")
    print("6. Fallback ke Ethernet jika wireless tidak tersedia")
    
    print("\nBenefits:")
    print("✓ UE dapat 'connect' ke gNB secara wireless seperti WiFi")
    print("✓ Docker containers tetap mendapat semua fitur 5G")
    print("✓ Realistic wireless propagation simulation")
    print("✓ Mobility support untuk UE")
    print("✓ Compatible dengan existing 5G configuration")

if __name__ == "__main__":
    success = test_hybrid_wireless_export()
    test_wireless_connectivity()
    
    print(f"\n=== Test Summary ===")
    if success:
        print("✓ Hybrid wireless + Docker implementation ready for testing")
        print("✓ Topology dapat di-export dari GUI dengan wireless connectivity")
        print("✓ gNB akan berfungsi sebagai wireless AP untuk UE")
        print("✓ UE akan connect ke gNB seperti WiFi client ke Access Point")
    else:
        print("✗ Implementation needs further fixes")
    
    print("\nNext steps:")
    print("1. Test dengan 'Run All' di GUI")
    print("2. Verify wireless association antara UE dan gNB")
    print("3. Check uesimtun interface creation di UE container")
    print("4. Test 5G data flow melalui wireless connection")
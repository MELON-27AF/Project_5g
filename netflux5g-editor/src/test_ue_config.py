#!/usr/bin/env python3
"""
Quick test to check UE config generation
"""

import sys
import os
sys.path.append('.')
sys.path.append('./export')

# Import the necessary modules
from export.mininet_export import MininetExporter

def test_ue_config():
    """Test UE config generation"""
    me = MininetExporter(None)
    
    # Test config
    ue_config = {
        'mcc': '999', 
        'mnc': '70', 
        'msisdn': '0000000001'
    }
    
    content = me.generate_ue_config_content(ue_config, 1)
    
    print("Generated UE config content:")
    print("=" * 50)
    print(content)
    print("=" * 50)
    print()
    
    # Check the gnbSearchList section specifically
    print("gnbSearchList section:")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'gnbSearchList' in line:
            print(f"Line {i+1}: {line}")
            if i+1 < len(lines):
                print(f"Line {i+2}: {lines[i+1]}")
            break
    
    print()
    
    # Check if placeholder is present
    if 'GNB_CONTAINER_IP_PLACEHOLDER' in content:
        print("✓ Placeholder 'GNB_CONTAINER_IP_PLACEHOLDER' found in content")
    else:
        print("✗ Placeholder 'GNB_CONTAINER_IP_PLACEHOLDER' NOT found in content")
        
    # Check for hardcoded IPs
    if '10.0.0.1' in content:
        print("✗ Hardcoded IP '10.0.0.1' found in content")
    if '127.0.0.1' in content:
        print("✗ Hardcoded IP '127.0.0.1' found in content")

if __name__ == "__main__":
    test_ue_config()

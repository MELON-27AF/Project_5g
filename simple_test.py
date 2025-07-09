#!/usr/bin/env python3
"""
Simple test to verify switch creation logic
"""

import sys
import os

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'netflux5g-editor', 'src'))

# Force reload of modules
if 'export.mininet_export' in sys.modules:
    del sys.modules['export.mininet_export']

try:
    from export.mininet_export import MininetExporter
    print("✓ Import successful")
    
    class MockMainWindow:
        pass
    
    mock_window = MockMainWindow()
    exporter = MininetExporter(mock_window)
    print("✓ MininetExporter instantiated")
    
    # Check if method exists
    if hasattr(exporter, 'configure_switch_behavior'):
        print("✓ configure_switch_behavior method found!")
        exporter.configure_switch_behavior(auto_default=False, auto_management=False)
        print("✓ Method executed successfully")
        print(f"  Default switch creation: {exporter.auto_create_default_switch}")
        print(f"  Management switch creation: {exporter.auto_create_management_switch}")
    else:
        print("✗ configure_switch_behavior method NOT found")
        print("Available methods:")
        methods = [m for m in dir(exporter) if not m.startswith('_') and callable(getattr(exporter, m))]
        for method in sorted(methods):
            print(f"  - {method}")
        
    # Test categorization logic
    print("\n=== Testing Categorization Logic ===")
    
    # Create test nodes (similar to basic topology)
    test_nodes = [
        {'name': 'UE #1', 'type': 'UE', 'x': 100, 'y': 100, 'properties': {}},
        {'name': 'UE #2', 'type': 'UE', 'x': 200, 'y': 100, 'properties': {}},
        {'name': 'GNB #1', 'type': 'GNB', 'x': 150, 'y': 200, 'properties': {}},
        {'name': 'VGcore #1', 'type': 'VGcore', 'x': 150, 'y': 300, 'properties': {}},
    ]
    
    test_links = [
        {'from': 'GNB #1', 'to': 'VGcore #1'}
    ]
    
    categorized = exporter.categorize_nodes(test_nodes)
    print(f"✓ Categorized {len(test_nodes)} nodes:")
    for category, nodes in categorized.items():
        if nodes:
            print(f"  - {category}: {len(nodes)} items")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

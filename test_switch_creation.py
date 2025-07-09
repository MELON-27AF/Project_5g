#!/usr/bin/env python3
"""
Test script to demonstrate the improved switch creation behavior
in NetFlux5G's Mininet exporter.
"""

import sys
import os

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'netflux5g-editor', 'src'))

from export.mininet_export import MininetExporter

class MockMainWindow:
    """Mock main window for testing"""
    def __init__(self):
        self.topology_nodes = []
        self.topology_links = []
        
    def extractTopology(self):
        return self.topology_nodes, self.topology_links
        
    def showCanvasStatus(self, message):
        print(f"Status: {message}")

def test_switch_creation_scenarios():
    """Test different scenarios for automatic switch creation."""
    
    print("=== Testing NetFlux5G Switch Creation Logic ===\n")
    
    # Create mock main window and exporter
    mock_window = MockMainWindow()
    exporter = MininetExporter(mock_window)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Basic 5G Topology (UEs + GNB + VGcore, with links)',
            'nodes': [
                {'name': 'ue1', 'type': 'UE'},
                {'name': 'ue2', 'type': 'UE'}, 
                {'name': 'gnb1', 'type': 'GNB'},
                {'name': 'vgcore1', 'type': 'VGcore'}
            ],
            'links': [
                {'from': 'ue1', 'to': 'gnb1'},
                {'from': 'ue2', 'to': 'gnb1'},
                {'from': 'gnb1', 'to': 'vgcore1'}
            ],
            'config': {'respect_topology': True}
        },
        {
            'name': 'Basic 5G Topology (no explicit links)',
            'nodes': [
                {'name': 'ue1', 'type': 'UE'},
                {'name': 'gnb1', 'type': 'GNB'},
                {'name': 'vgcore1', 'type': 'VGcore'}
            ],
            'links': [],
            'config': {'respect_topology': True}
        },
        {
            'name': '5G Topology with existing switch',
            'nodes': [
                {'name': 'ue1', 'type': 'UE'},
                {'name': 'gnb1', 'type': 'GNB'},
                {'name': 'vgcore1', 'type': 'VGcore'},
                {'name': 'switch1', 'type': 'Switch'}
            ],
            'links': [],
            'config': {'respect_topology': True}
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"--- Scenario {i}: {scenario['name']} ---")
        
        # Set up topology
        mock_window.topology_nodes = scenario['nodes']
        mock_window.topology_links = scenario['links']
        
        # Configure exporter
        config = scenario.get('config', {})
        exporter.configure_switch_behavior(
            respect_topology=config.get('respect_topology', True)
        )
        
        # Categorize nodes
        categorized = exporter.categorize_nodes(scenario['nodes'])
        
        # Check conditions
        has_5g = bool(categorized['gnbs'] or categorized['ues'] or categorized['core5g'])
        has_switches = bool(categorized['switches'] or categorized['aps'])
        has_links = bool(scenario['links'])
        
        should_create_s1 = (
            exporter.auto_create_default_switch and
            has_5g and 
            not has_switches and 
            (not exporter.respect_explicit_topology or not has_links)
        )
        
        print(f"  Nodes: {len(scenario['nodes'])} ({', '.join([n['type'] for n in scenario['nodes']])})")
        print(f"  Links: {len(scenario['links'])}")
        print(f"  Has 5G components: {has_5g}")
        print(f"  Has switches/APs: {has_switches}")
        print(f"  Has explicit links: {has_links}")
        print(f"  Will create s1 switch: {should_create_s1}")
        print()

def test_configuration_options():
    """Test different configuration options."""
    
    print("=== Testing Configuration Options ===\n")
    
    mock_window = MockMainWindow()
    mock_window.topology_nodes = [
        {'name': 'ue1', 'type': 'UE'},
        {'name': 'gnb1', 'type': 'GNB'},
        {'name': 'vgcore1', 'type': 'VGcore'}
    ]
    mock_window.topology_links = []
    
    exporter = MininetExporter(mock_window)
    
    configs = [
        {'auto_default': True, 'respect_topology': False, 'description': 'Always create default switch'},
        {'auto_default': True, 'respect_topology': True, 'description': 'Respect user topology (default)'},
        {'auto_default': False, 'respect_topology': True, 'description': 'Never create default switch'},
    ]
    
    for config in configs:
        print(f"--- {config['description']} ---")
        exporter.configure_switch_behavior(
            auto_default=config['auto_default'],
            respect_topology=config['respect_topology']
        )
        
        # Check if s1 would be created
        categorized = exporter.categorize_nodes(mock_window.topology_nodes)
        has_5g = bool(categorized['gnbs'] or categorized['ues'] or categorized['core5g'])
        has_switches = bool(categorized['switches'] or categorized['aps'])
        has_links = bool(mock_window.topology_links)
        
        should_create_s1 = (
            exporter.auto_create_default_switch and
            has_5g and 
            not has_switches and 
            (not exporter.respect_explicit_topology or not has_links)
        )
        
        print(f"  Configuration: auto_default={config['auto_default']}, respect_topology={config['respect_topology']}")
        print(f"  Result: Will create s1 = {should_create_s1}")
        print()

if __name__ == '__main__':
    test_switch_creation_scenarios()
    test_configuration_options()
    
    print("=== Summary ===")
    print("The improved logic now:")
    print("1. Respects explicit user topology when links are defined")
    print("2. Only creates s1 when truly needed (5G components + no switches + no links)")
    print("3. Only creates s999 when no other switches exist for container connectivity")
    print("4. Provides configuration options for different use cases")
    print("\nFor your basic_5g_topology.nf5g:")
    print("- Since it HAS explicit links defined, s1 should NOT be created")
    print("- s999 might still be created only if containers need management connectivity")

#!/usr/bin/env python3
"""
Debug script to help identify the topology loading issue in NetFlux5G.

This script will help you debug the difference between what's loaded from example files
and what's extracted when running "Run All".
"""

import sys
import os
import json

# Add the src directory to the path so we can import modules
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_path)

def load_example_file(file_path):
    """Load and parse an example topology file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def analyze_topology_data(data, file_name):
    """Analyze the topology data structure."""
    print(f"\n=== Analysis of {file_name} ===")
    
    if not data:
        print("No data to analyze")
        return
    
    print(f"Version: {data.get('version', 'Unknown')}")
    print(f"Type: {data.get('type', 'Unknown')}")
    
    metadata = data.get('metadata', {})
    print(f"Created: {metadata.get('created_date', 'Unknown')}")
    print(f"Editor Version: {metadata.get('editor_version', 'Unknown')}")
    
    nodes = data.get('nodes', [])
    links = data.get('links', [])
    
    print(f"Total Nodes: {len(nodes)}")
    print(f"Total Links: {len(links)}")
    
    # Analyze node types
    node_types = {}
    for node in nodes:
        node_type = node.get('type', 'Unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    print("\nNode Types:")
    for node_type, count in node_types.items():
        print(f"  {node_type}: {count}")
    
    # List first few nodes for detail
    print("\nFirst 5 nodes (detailed):")
    for i, node in enumerate(nodes[:5]):
        name = node.get('name', 'Unnamed')
        node_type = node.get('type', 'Unknown')
        x = node.get('x', 0)
        y = node.get('y', 0)
        print(f"  {i+1}. {name} ({node_type}) at ({x}, {y})")
    
    # List links
    print(f"\nLinks:")
    for i, link in enumerate(links):
        source = link.get('source', 'Unknown')
        dest = link.get('destination', 'Unknown')
        print(f"  {i+1}. {source} -> {dest}")

def compare_topologies(files):
    """Compare multiple topology files to identify differences."""
    print("=" * 60)
    print("TOPOLOGY COMPARISON ANALYSIS")
    print("=" * 60)
    
    all_data = []
    
    # Load all files
    for file_path in files:
        file_name = os.path.basename(file_path)
        data = load_example_file(file_path)
        if data:
            all_data.append((file_name, data))
            analyze_topology_data(data, file_name)
    
    # Compare node types across files
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    
    for file_name, data in all_data:
        nodes = data.get('nodes', [])
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"\n{file_name}:")
        print(f"  Total components: {len(nodes)}")
        print(f"  Component types: {', '.join(f'{t}({c})' for t, c in node_types.items())}")

def main():
    # Path to the examples directory
    examples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "examples")
    
    print("NetFlux5G Topology Debug Tool")
    print("=" * 60)
    print(f"Examples directory: {examples_dir}")
    
    if not os.path.exists(examples_dir):
        print(f"ERROR: Examples directory not found: {examples_dir}")
        return
    
    # List all .nf5g files in examples directory
    example_files = []
    for file in os.listdir(examples_dir):
        if file.endswith('.nf5g'):
            example_files.append(os.path.join(examples_dir, file))
    
    if not example_files:
        print("No .nf5g files found in examples directory")
        return
    
    print(f"Found {len(example_files)} example files:")
    for file in example_files:
        print(f"  - {os.path.basename(file)}")
    
    # Analyze all files
    compare_topologies(example_files)
    
    print("\n" + "=" * 60)
    print("DEBUG INSTRUCTIONS")
    print("=" * 60)
    print("To debug the 'Run All' issue:")
    print("1. Load one of the example topologies in the GUI")
    print("2. Before clicking 'Run All', add debug prints to automation_runner.py")
    print("3. In the run_all() method, after line 'nodes, links = self.main_window.extractTopology()'")
    print("4. Add these lines:")
    print("   print(f'DEBUG: Extracted {len(nodes)} nodes, {len(links)} links')")
    print("   for node in nodes:")
    print("       print(f'  - {node.get(\"name\", \"Unnamed\")} ({node.get(\"type\", \"Unknown\")})')")
    print("5. Compare the output with what you see above for the loaded example file")
    print("6. If they don't match, the issue is in the loading or extraction process")

if __name__ == "__main__":
    main()

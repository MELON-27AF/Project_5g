#!/usr/bin/env python3
"""
Test script to debug topology loading and extraction issues.
Run this after loading each example topology to compare expected vs actual.
"""

import sys
import os
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def analyze_nf5g_file(filepath):
    """Analyze a .nf5g file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        print(f"\n=== Analysis of {os.path.basename(filepath)} ===")
        print(f"Version: {data.get('version', 'Unknown')}")
        print(f"Type: {data.get('type', 'Unknown')}")
        print(f"Created: {data.get('created', 'Unknown')}")
        print(f"Editor Version: {data.get('editor_version', 'Unknown')}")
        
        nodes = data.get('nodes', [])
        links = data.get('links', [])
        
        print(f"Total Nodes: {len(nodes)}")
        print(f"Total Links: {len(links)}")
        
        # Count node types
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("\nNode Types:")
        for node_type, count in node_types.items():
            print(f"  {node_type}: {count}")
        
        print(f"\nFirst 5 nodes (detailed):")
        for i, node in enumerate(nodes[:5]):
            name = node.get('name', 'Unnamed')
            node_type = node.get('type', 'Unknown')
            x = node.get('x', 0)
            y = node.get('y', 0)
            print(f"  {i+1}. {name} ({node_type}) at ({x}, {y})")
        
        if links:
            print(f"\nLinks:")
            for i, link in enumerate(links):
                source = link.get('source', 'Unknown')
                dest = link.get('destination', 'Unknown')
                print(f"  {i+1}. {source} -> {dest}")
        
        return data
        
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None

def main():
    print("NetFlux5G Topology Loading Test")
    print("=" * 50)
    
    examples_dir = os.path.join(os.path.dirname(__file__), 'src', 'examples')
    if not os.path.exists(examples_dir):
        print(f"Examples directory not found: {examples_dir}")
        return
    
    print(f"Examples directory: {examples_dir}")
    
    # Find all .nf5g files
    nf5g_files = [f for f in os.listdir(examples_dir) if f.endswith('.nf5g')]
    print(f"Found {len(nf5g_files)} example files:")
    for f in nf5g_files:
        print(f"  - {f}")
    
    print("\n" + "=" * 50)
    print("INSTRUCTIONS FOR DEBUGGING:")
    print("=" * 50)
    print("1. Run this script to see what's in each example file")
    print("2. Start the NetFlux5G GUI")
    print("3. Load one of the example topologies")
    print("4. Click 'Run All' and observe the debug output in the terminal")
    print("5. Compare the 'Extracted topology' output with the expected content above")
    print("6. If they don't match, the issue is in the loading process")
    print("7. If they do match, the issue is in the mininet export process")
    
    # Analyze each file
    all_data = {}
    for filename in sorted(nf5g_files):
        filepath = os.path.join(examples_dir, filename)
        data = analyze_nf5g_file(filepath)
        if data:
            all_data[filename] = data
    
    print("\n" + "=" * 50)
    print("COMPARISON SUMMARY")
    print("=" * 50)
    
    for filename, data in all_data.items():
        nodes = data.get('nodes', [])
        links = data.get('links', [])
        
        # Count node types
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"\n{filename}:")
        print(f"  Total components: {len(nodes)}")
        type_summary = ", ".join([f"{t}({c})" for t, c in node_types.items()])
        print(f"  Component types: {type_summary}")

if __name__ == "__main__":
    main()

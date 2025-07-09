"""
Enhanced Mininet-WiFi Export with Dynamic UI Configuration Support

This module generates working mininet-wifi scripts that dynamically use the properties
configured in the NetFlux5G UI. It supports:

- Standard mininet-wifi components (APs, STAs, Hosts)
- 5G components (gNBs, UEs with UERANSIM integration)
- Docker containers for 5G core functions
- Dynamic property mapping from UI to script parameters
- Proper mininet-wifi/containernet integration

The generated scripts follow mininet-wifi best practices and are compatible with
the mininet-wifi examples structure.
"""

import os
import re
import shutil
import traceback
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QDateTime
from manager.configmap import ConfigurationMapper
from manager.debug import debug_print, error_print, warning_print

class MininetExporter:
    """Handler for exporting network topology to Mininet scripts with Level 2 features."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
        # Configuration options for switch creation behavior
        self.auto_create_default_switch = True  # Create s1 when no switches/APs exist
        self.auto_create_management_switch = True  # Create s999 for container connectivity
        self.respect_explicit_topology = True  # Don't create default switches if user has defined links
        
    def configure_switch_behavior(self, auto_default=True, auto_management=True, respect_topology=True):
        """Configure automatic switch creation behavior.
        
        Args:
            auto_default (bool): Automatically create s1 switch for 5G components when no switches exist
            auto_management (bool): Automatically create s999 management switch for unconnected containers  
            respect_topology (bool): Don't create default switches if user has defined explicit links
        """
        self.auto_create_default_switch = auto_default
        self.auto_create_management_switch = auto_management
        self.respect_explicit_topology = respect_topology
        
        debug_print(f"DEBUG: Switch creation configured - default:{auto_default}, management:{auto_management}, respect_topology:{respect_topology}")
        
    def export_to_mininet(self, skip_save_check=False):
        """Export the current topology to a Mininet script.
        
        This method first checks if there are unsaved changes or if the topology
        hasn't been saved to a file yet. If so, it prompts the user to save first
        to ensure proper Docker network naming and configuration consistency.
        
        Args:
            skip_save_check (bool): If True, skip the unsaved changes check.
                                   Useful for automated exports.
        """
        # Check for unsaved changes or unsaved file (unless skipped)
        if not skip_save_check and not self._check_save_status():
            return  # User cancelled or chose not to proceed
        
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window, 
            "Export to Mininet Script", 
            "", 
            "Python Files (*.py);;All Files (*)"
        )
        if filename:
            self.export_to_mininet_script(filename)

    def export_to_mininet_script(self, filename):
        """Export the current topology to a working Mininet-WiFi Python script."""
        nodes, links = self.main_window.extractTopology()
        
        print(f"DEBUG: MininetExporter - Got {len(nodes)} nodes, {len(links)} links for export")
        print("DEBUG: MininetExporter - Node details:")
        for node in nodes:
            name = node.get('name', 'Unnamed')
            node_type = node.get('type', 'Unknown')
            print(f"  - {name} ({node_type})")
        
        if not nodes:
            self.main_window.showCanvasStatus("No components found to export!")
            return
        
        # Categorize nodes by type for proper script generation
        categorized_nodes = self.categorize_nodes(nodes)
        
        print(f"DEBUG: MininetExporter - Categorized nodes:")
        for category, items in categorized_nodes.items():
            if items:
                print(f"  {category}: {len(items)} items")
        
        try:
            with open(filename, "w") as f:
                self.write_mininet_script(f, nodes, links, categorized_nodes)
            
            print(f"DEBUG: MininetExporter - Successfully wrote script to {filename}")
            
            # Create config files for 5G components
            if categorized_nodes.get('core5g') or categorized_nodes.get('core5g_components'):
                self.create_config_files(filename, categorized_nodes)
            
            self.main_window.showCanvasStatus(f"Exported topology to {os.path.basename(filename)}")
            debug_print(f"DEBUG: Exported {len(nodes)} nodes and {len(links)} links to {filename}")
            
        except Exception as e:
            error_msg = f"Error exporting to Mininet: {str(e)}"
            self.main_window.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()

    def categorize_nodes(self, nodes):
        """Categorize nodes by type for proper script generation."""
        categorized = {
            'hosts': [n for n in nodes if n['type'] in ['Host']],
            'stas': [n for n in nodes if n['type'] == 'STA'],
            'ues': [n for n in nodes if n['type'] == 'UE'],
            'gnbs': [n for n in nodes if n['type'] == 'GNB'],
            'aps': [n for n in nodes if n['type'] == 'AP'],
            'switches': [n for n in nodes if n['type'] in ['Switch', 'Router']],
            'controllers': [n for n in nodes if n['type'] == 'Controller'],
            'docker_hosts': [n for n in nodes if n['type'] == 'DockerHost'],
            'core5g': [n for n in nodes if n['type'] == 'VGcore']
        }
        
        # Extract 5G core components from VGcore configurations
        categorized['core5g_components'] = self.extract_5g_components_by_type(categorized['core5g'])
        
        return categorized

    def write_mininet_script(self, f, nodes, links, categorized_nodes):
        """Write the complete Mininet-WiFi script following best practices."""
        # Write script header
        self.write_script_header(f)
        
        # Write imports based on components used
        self.write_imports(f, categorized_nodes)
        
        # Write utility functions
        self.write_utility_functions(f)
        
        # Write topology function
        self.write_topology_function(f, nodes, links, categorized_nodes)
        
        # Write main execution
        self.write_main_execution(f)

    def write_script_header(self, f):
        """Write the script header with metadata."""
        f.write('#!/usr/bin/env python\n\n')
        f.write('"""\n')
        f.write('NetFlux5G - Mininet-WiFi Topology\n')
        f.write('Generated by NetFlux5G Editor\n')
        f.write(f'Generated on: {QDateTime.currentDateTime().toString()}\n')
        
        # Add Docker network information if available
        if hasattr(self.main_window, 'docker_network_manager'):
            network_name = self.main_window.docker_network_manager.get_current_network_name()
            if network_name:
                f.write(f'Docker Network: {network_name}\n')
        
        f.write('\n')
        f.write('This script creates a network topology using mininet-wifi\n')
        f.write('with dynamic configuration from the NetFlux5G UI.\n')
        f.write('\n')
        f.write('Network Mode Configuration:\n')
        f.write('- 5G components (UEs, gNBs, VGCore) will use the Docker network\n')
        f.write('  derived from the topology filename\n')
        
        # Get dynamic network name for documentation
        if hasattr(self.main_window, 'docker_network_manager'):
            network_name = self.main_window.docker_network_manager.get_current_network_name()
            if network_name:
                f.write(f'- Current network mode: {network_name}\n')
            else:
                f.write('- Default network mode: open5gs-ueransim_default (when no file loaded)\n')
        else:
            f.write('- Default network mode: open5gs-ueransim_default\n')
        
        # Add Docker network usage note
        if hasattr(self.main_window, 'docker_network_manager'):
            network_name = self.main_window.docker_network_manager.get_current_network_name()
            if network_name:
                f.write('\n')
                f.write('Docker Network Usage:\n')
                f.write(f'- Network Name: {network_name}\n')
                f.write('- Type: Bridge network with attachable containers\n')
                f.write('- Create network: docker network create --driver bridge --attachable ' + network_name + '\n')
                f.write('- Delete network: docker network rm ' + network_name + '\n')
        
        f.write('"""\n\n')

    def write_imports(self, f, categorized_nodes):
        """Write necessary imports with circular import avoidance strategy."""
        f.write('import sys\n')
        f.write('import os\n')
        f.write('from subprocess import call\n')
        f.write('\n')
        
        # Check if we need wireless functionality
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        
        # Check if we need containernet for Docker/5G components
        has_docker = (categorized_nodes['docker_hosts'] or categorized_nodes['ues'] or 
                     categorized_nodes['gnbs'] or categorized_nodes['core5g'])
        
        # Initialize availability flags and apply compatibility patches
        f.write('# Network capability detection and compatibility patches\n')
        f.write('WIFI_AVAILABLE = False\n')
        f.write('CONTAINERNET_AVAILABLE = False\n')
        f.write('\n')
        f.write('# Apply compatibility patches for missing functions\n')
        f.write('def apply_compatibility_patches():\n')
        f.write('    """Apply compatibility patches for missing mininet functions"""\n')
        f.write('    try:\n')
        f.write('        import mininet.util\n')
        f.write('        if not hasattr(mininet.util, "fmtBps"):\n')
        f.write('            def fmtBps(bps):\n')
        f.write('                """Format bandwidth in bits per second"""\n')
        f.write('                if bps is None:\n')
        f.write('                    return "None"\n')
        f.write('                if bps < 1e3:\n')
        f.write('                    return f"{bps:.2f} bps"\n')
        f.write('                elif bps < 1e6:\n')
        f.write('                    return f"{bps/1e3:.2f} Kbps"\n')
        f.write('                elif bps < 1e9:\n')
        f.write('                    return f"{bps/1e6:.2f} Mbps"\n')
        f.write('                elif bps < 1e12:\n')
        f.write('                    return f"{bps/1e9:.2f} Gbps"\n')
        f.write('                else:\n')
        f.write('                    return f"{bps/1e12:.2f} Tbps"\n')
        f.write('            mininet.util.fmtBps = fmtBps\n')
        f.write('            print("✓ Patched mininet.util.fmtBps")\n')
        f.write('    except ImportError:\n')
        f.write('        pass\n')
        f.write('\n')
        f.write('# Apply patches before importing network modules\n')
        f.write('apply_compatibility_patches()\n')
        f.write('\n')
        
        # Import strategy optimized for Docker containers with 5G components
        # Strategy 1: Try containernet first if needed (best for Docker containers)
        if has_docker:
            f.write('# Try containernet first for Docker support\n')
            f.write('try:\n')
            f.write('    from containernet.net import Containernet\n')
            f.write('    from containernet.node import DockerSta\n')
            f.write('    from mininet.node import RemoteController, OVSKernelSwitch, Host, Node\n')
            f.write('    from mininet.log import setLogLevel, info\n')
            f.write('    from containernet.cli import CLI\n')
            f.write('    from mininet.link import TCLink, Link, Intf\n')
            f.write('    from containernet.term import makeTerm as makeTerm2\n')
            f.write('    CONTAINERNET_AVAILABLE = True\n')
            f.write('    print("✓ containernet available - using Docker support")\n')
            f.write('except ImportError as e:\n')
            f.write('    print(f"Warning: containernet import failed: {e}")\n')
            f.write('    CONTAINERNET_AVAILABLE = False\n')
            f.write('\n')
            
            # Also try mininet-wifi with containernet for wireless + Docker
            f.write('# Try mininet-wifi with containernet for wireless + Docker support\n')
            f.write('if CONTAINERNET_AVAILABLE:\n')
            f.write('    try:\n')
            f.write('        from mn_wifi.net import Mininet_wifi\n')
            f.write('        from mn_wifi.node import Station, OVSKernelAP\n')
            f.write('        from mn_wifi.link import wmediumd\n')
            f.write('        from mn_wifi.wmediumdConnector import interference\n')
            f.write('        WIFI_AVAILABLE = True\n')
            f.write('        print("✓ mininet-wifi + containernet available - full wireless Docker support")\n')
            f.write('    except ImportError as e:\n')
            f.write('        print(f"Note: mininet-wifi not available with containernet: {e}")\n')
            f.write('        WIFI_AVAILABLE = False\n')
            f.write('\n')
        
        # Strategy 2: Try mininet-wifi only if containernet is not available or not needed
        if has_wireless:
            f.write('# Try mininet-wifi for wireless support (if containernet not available)\n')
            f.write('if not CONTAINERNET_AVAILABLE:\n')
            f.write('    try:\n')
            f.write('        from mn_wifi.net import Mininet_wifi\n')
            f.write('        from mn_wifi.node import Station, OVSKernelAP\n')
            f.write('        from mn_wifi.link import wmediumd\n')
            f.write('        from mn_wifi.wmediumdConnector import interference\n')
            f.write('        from mininet.node import RemoteController, OVSKernelSwitch, Host, Node\n')
            f.write('        from mininet.log import setLogLevel, info\n')
            f.write('        from mininet.cli import CLI\n')
            f.write('        from mininet.link import TCLink, Link, Intf\n')
            f.write('        WIFI_AVAILABLE = True\n')
            f.write('        print("✓ mininet-wifi available - using wireless support")\n')
            f.write('    except ImportError as e:\n')
            f.write('        print(f"Warning: mininet-wifi import failed: {e}")\n')
            f.write('        print("Falling back to standard Mininet")\n')
            f.write('        WIFI_AVAILABLE = False\n')
            f.write('\n')
        
        # Strategy 3: Standard Mininet fallback
        f.write('# Standard Mininet fallback (always import if others failed)\n')
        f.write('if not CONTAINERNET_AVAILABLE and not WIFI_AVAILABLE:\n')
        f.write('    try:\n')
        f.write('        from mininet.net import Mininet\n')
        f.write('        from mininet.node import RemoteController, OVSKernelSwitch, Host, Node\n')
        f.write('        from mininet.log import setLogLevel, info\n')
        f.write('        from mininet.cli import CLI\n')
        f.write('        from mininet.link import TCLink, Link, Intf\n')
        f.write('        print("✓ Using standard Mininet")\n')
        f.write('    except ImportError as e:\n')
        f.write('        print(f"ERROR: Cannot import any Mininet variant: {e}")\n')
        f.write('        sys.exit(1)\n')
        f.write('\n')
        
        # Define fallback classes for missing components
        if has_wireless:
            f.write('# Define fallback classes for wireless components\n')
            f.write('if not WIFI_AVAILABLE:\n')
            f.write('    # Create fallback classes when mininet-wifi is not available\n')
            f.write('    Station = Host  # Use Host as Station fallback\n')
            f.write('    OVSKernelAP = OVSKernelSwitch  # Use OVSSwitch as AP fallback\n')
            f.write('    wmediumd = None\n')
            f.write('    interference = None\n')
            f.write('\n')
        
        if has_docker:
            f.write('# Define fallback classes for Docker components\n')
            f.write('if not CONTAINERNET_AVAILABLE:\n')
            f.write('    # Create fallback classes when containernet is not available\n')
            f.write('    Docker = Host  # Use Host as Docker fallback\n')
            f.write('    \n')
            f.write('    class Containernet(Mininet):\n')
            f.write('        """Fallback Containernet class using standard Mininet"""\n')
            f.write('        def addDocker(self, name, **kwargs):\n')
            f.write('            """Fallback addDocker method"""\n')
            f.write('            # Filter out Docker-specific parameters\n')
            f.write('            filtered_kwargs = {}\n')
            f.write('            for key, value in kwargs.items():\n')
            f.write('                if key not in ["dimage", "dcmd", "network_mode", "cap_add", \n')
            f.write('                               "devices", "privileged", "publish_all_ports", \n')
            f.write('                               "volumes", "environment"]:\n')
            f.write('                    filtered_kwargs[key] = value\n')
            f.write('            return self.addHost(name, cls=Host, **filtered_kwargs)\n')
            f.write('    \n')
            f.write('    def makeTerm2(node, cmd="bash"):\n')
            f.write('        """Fallback makeTerm2 function"""\n')
            f.write('        print(f"*** Starting process on {node.name}: {cmd}")\n')
            f.write('        # Use sendCmd for background processes\n')
            f.write('        node.sendCmd(cmd)\n')
            f.write('\n')

    def write_utility_functions(self, f):
        """Write utility functions for the script."""
        f.write('def sanitize_name(name):\n')
        f.write('    """Convert display name to valid Python variable name."""\n')
        f.write('    import re\n')
        f.write('    # Remove special characters and spaces\n')
        f.write('    clean_name = re.sub(r\'[^a-zA-Z0-9_]\', \'_\', name)\n')
        f.write('    # Ensure it starts with a letter or underscore\n')
        f.write('    if clean_name and clean_name[0].isdigit():\n')
        f.write('        clean_name = \'_\' + clean_name\n')
        f.write('    return clean_name or \'node\'\n\n')
        
        f.write('def add_node_to_network(net, node_name, **kwargs):\n')
        f.write('    """Add node to network using appropriate method based on network type and parameters."""\n')
        f.write('    # Check if this should be a Docker container\n')
        f.write('    if CONTAINERNET_AVAILABLE and "dimage" in kwargs:\n')
        f.write('        # Use containernet addDocker method\n')
        f.write('        docker_kwargs = {}\n')
        f.write('        # Map parameters to addDocker format\n')
        f.write('        for key, value in kwargs.items():\n')
        f.write('            if key == "dimage":\n')
        f.write('                docker_kwargs["dimage"] = value\n')
        f.write('            elif key == "dcmd":\n')
        f.write('                docker_kwargs["dcmd"] = value\n')
        f.write('            elif key in ["volumes", "environment", "cap_add", "devices", "privileged", "network_mode", "publish_all_ports"]:\n')
        f.write('                docker_kwargs[key] = value\n')
        f.write('            elif key == "position":\n')
        f.write('                # Position might not be supported in addDocker\n')
        f.write('                continue\n')
        f.write('            # Skip wireless-specific params like range, txpower for Docker\n')
        f.write('        return net.addDocker(node_name, **docker_kwargs)\n')
        f.write('    elif hasattr(net, "addStation"):\n')
        f.write('        # mininet-wifi is available, use addStation\n')
        f.write('        return net.addStation(node_name, **kwargs)\n')
        f.write('    else:\n')
        f.write('        # Standard Mininet, use addHost and filter parameters\n')
        f.write('        filtered_kwargs = {}\n')
        f.write('        supported_params = ["cls", "ip", "mac", "inNamespace"]\n')
        f.write('        for key, value in kwargs.items():\n')
        f.write('            if key in supported_params:\n')
        f.write('                filtered_kwargs[key] = value\n')
        f.write('            elif key in ["position", "range", "txpower", "associationMode", "dimage", "dcmd",\n')
        f.write('                        "network_mode", "cap_add", "devices", "privileged",\n')
        f.write('                        "publish_all_ports", "volumes", "environment"]:\n')
        f.write('                # Skip Docker and wireless-specific parameters\n')
        f.write('                continue\n')
        f.write('        return net.addHost(node_name, **filtered_kwargs)\n\n')
        
        # Add Docker network utility functions if needed
        network_name = None
        if hasattr(self.main_window, 'docker_network_manager'):
            network_name = self.main_window.docker_network_manager.get_current_network_name()
        
        if not network_name:
            network_name = "open5gs-ueransim_default"  # fallback network name
            
        f.write('def create_docker_network_if_needed():\n')
        f.write('    """Create Docker network if it doesn\'t exist."""\n')
        f.write('    import subprocess\n')
        f.write(f'    network_name = "{network_name}"\n')
        f.write('    \n')
        f.write('    try:\n')
        f.write('        # Check if network exists\n')
        f.write('        result = subprocess.run(["docker", "network", "ls", "--filter", f"name=^{network_name}$", "--format", "{{.Name}}"],\n')
        f.write('                              capture_output=True, text=True, check=True)\n')
        f.write('        \n')
        f.write('        existing_networks = result.stdout.strip().split("\\n")\n')
        f.write('        if network_name not in existing_networks or not result.stdout.strip():\n')
        f.write('            print(f"*** Creating Docker network: {network_name}")\n')
        f.write('            create_result = subprocess.run(["docker", "network", "create", "--driver", "bridge", "--attachable", network_name], \n')
        f.write('                                         capture_output=True, text=True, check=True)\n')
        f.write('            print(f"*** Docker network {network_name} created successfully")\n')
        f.write('        else:\n')
        f.write(f'            print(f"*** Using existing Docker network: {network_name}")\n')
        f.write('    except subprocess.CalledProcessError as e:\n')
        f.write('        print(f"Warning: Error managing Docker network: {e}")\n')
        f.write('        if e.stderr:\n')
        f.write('            print(f"Error details: {e.stderr}")\n')
        f.write('        print("Note: Containers may fail to start if network is not available")\n')
        f.write('    except FileNotFoundError:\n')
        f.write('        print("Warning: Docker command not found. Please ensure Docker is installed and running.")\n')
        f.write('        print("Note: Containers may fail to start if Docker is not available")\n')
        f.write('\n')
        
        f.write('def check_docker_image(image_name):\n')
        f.write('    """Check if Docker image exists locally or can be pulled."""\n')
        f.write('    import subprocess\n')
        f.write('    try:\n')
        f.write('        # Check if image exists locally\n')
        f.write('        result = subprocess.run(["docker", "images", "-q", image_name], \n')
        f.write('                              capture_output=True, text=True, check=True)\n')
        f.write('        if result.stdout.strip():\n')
        f.write('            return True\n')
        f.write('        \n')
        f.write('        # Try to pull the image\n')
        f.write('        print(f"*** Pulling Docker image: {image_name}")\n')
        f.write('        pull_result = subprocess.run(["docker", "pull", image_name], \n')
        f.write('                                   capture_output=True, text=True, check=True)\n')
        f.write('        print(f"*** Successfully pulled: {image_name}")\n')
        f.write('        return True\n')
        f.write('    except subprocess.CalledProcessError as e:\n')
        f.write('        print(f"*** Warning: Cannot pull image {image_name}: {e}")\n')
        f.write('        if e.stderr:\n')
        f.write('            print(f"*** Error details: {e.stderr.strip()}")\n')
        f.write('        return False\n')
        f.write('    except FileNotFoundError:\n')
        f.write('        print("*** Warning: Docker command not found")\n')
        f.write('        return False\n')
        f.write('\n')

    def create_config_files(self, script_path, categorized_nodes):
        """Create config directory and generate/copy necessary config files for 5G components."""
        script_dir = os.path.dirname(script_path)
        config_dir = os.path.join(script_dir, "config")
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        debug_print(f"DEBUG: Created config directory: {config_dir}")
        
        # Path to the 5g-configs template directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_config_dir = os.path.join(current_dir, "5g-configs")
        
        # Collect required config files from 5G components
        config_files_created = 0
        
        # Check VGcore components for required configs
        for vgcore_node in categorized_nodes.get('core5g', []):
            components = categorized_nodes.get('core5g_components', {})
            for comp_type, comp_list in components.items():
                for component in comp_list:
                    config_file = component.get('config_file', f'{comp_type.lower()}.yaml')
                    dst_path = os.path.join(config_dir, config_file)
                    
                    # Check if destination exists and handle accordingly
                    if os.path.exists(dst_path):
                        if os.path.isdir(dst_path):
                            # Remove directory that should be a file
                            warning_print(f"WARNING: Removing directory that should be a file: {dst_path}")
                            shutil.rmtree(dst_path)
                        elif os.path.isfile(dst_path):
                            debug_print(f"DEBUG: Config file already exists: {config_file}")
                            continue
                    
                    # Check if component has imported config content
                    if component.get('imported') and component.get('config_content'):
                        self.write_imported_config(dst_path, component.get('config_content'))
                        debug_print(f"DEBUG: Created config from imported content: {config_file}")
                        config_files_created += 1
                    # Check if there's a config file path to copy from
                    elif component.get('config_file_path') and os.path.isfile(component.get('config_file_path')):
                        src_path = component.get('config_file_path')
                        shutil.copy2(src_path, dst_path)
                        debug_print(f"DEBUG: Copied config from path: {config_file}")
                        config_files_created += 1
                    # Try to copy from template directory
                    elif os.path.exists(template_config_dir):
                        src_path = os.path.join(template_config_dir, config_file)
                        if os.path.isfile(src_path):
                            shutil.copy2(src_path, dst_path)
                            debug_print(f"DEBUG: Copied config from template: {config_file}")
                            config_files_created += 1
                        else:
                            # Create a basic config file if template doesn't exist
                            self.create_basic_config_file(dst_path, config_file)
                            debug_print(f"DEBUG: Created basic config file: {config_file}")
                            config_files_created += 1
                    else:
                        # Create a basic config file as fallback
                        self.create_basic_config_file(dst_path, config_file)
                        debug_print(f"DEBUG: Created basic config file (fallback): {config_file}")
                        config_files_created += 1
        
        # Create UE configuration files
        ue_config_files = self.create_ue_config_files(config_dir, categorized_nodes)
        config_files_created += ue_config_files
        
        # Create gNB configuration files
        gnb_config_files = self.create_gnb_config_files(config_dir, categorized_nodes)
        config_files_created += gnb_config_files
        
        if config_files_created > 0:
            debug_print(f"DEBUG: Successfully created {config_files_created} config files")
        else:
            debug_print("DEBUG: No config files needed or found")
    
    def write_imported_config(self, file_path, config_content):
        """Write imported config content to a file."""
        try:
            if isinstance(config_content, dict):
                # If it's a dict, convert to YAML format
                try:
                    import yaml
                    with open(file_path, 'w') as f:
                        yaml.dump(config_content, f, default_flow_style=False)
                except ImportError:
                    # If PyYAML is not available, use a simple string representation
                    with open(file_path, 'w') as f:
                        f.write(str(config_content))
            else:
                # If it's already a string, write directly
                with open(file_path, 'w') as f:
                    f.write(str(config_content))
        except Exception as e:
            error_print(f"ERROR: Failed to write imported config to {file_path}: {e}")
            # Fall back to creating a basic config
            self.create_basic_config_file(file_path, os.path.basename(file_path))
    
    def create_basic_config_file(self, file_path, config_name):
        """Create a basic config file if template is missing."""
        component_type = config_name.replace('.yaml', '')
        
        basic_config = f"""# Basic {component_type.upper()} Configuration
# Generated by NetFlux5G
# This is a minimal configuration - customize as needed

db_uri: mongodb://mongodb:27017/open5gs
logger:
  level: info

{component_type}:
  sbi:
    - addr: 0.0.0.0
      port: 7777
  default:
    tac: 1
"""
        
        try:
            with open(file_path, 'w') as f:
                f.write(basic_config)
            debug_print(f"DEBUG: Created basic config file: {file_path}")
        except Exception as e:
            error_print(f"ERROR: Failed to create basic config file {file_path}: {e}")

    def write_topology_function(self, f, nodes, links, categorized_nodes):
        """Write the main topology function following mininet-wifi patterns.
        
        Network Mode Behavior:
        - When a topology file is loaded, the Docker network mode for 5G components 
          (UEs, gNBs, VGCore) is dynamically set based on the filename
        - Network name format: "netflux5g_{sanitized_filename}"
        - Falls back to "open5gs-ueransim_default" when no file is loaded
        """
        f.write('def topology(args):\n')
        f.write('    """Create network topology."""\n')
        f.write('    import os\n')
        f.write('    cwd = os.getcwd()  # Current Working Directory\n\n')
        
        # Get dynamic network name for 5G components
        dynamic_network_name = None
        if hasattr(self.main_window, 'docker_network_manager'):
            dynamic_network_name = self.main_window.docker_network_manager.get_current_network_name()
        
        # Add Docker network setup for any Docker components
        has_docker_components = (categorized_nodes.get('core5g') or 
                               categorized_nodes.get('docker_hosts') or
                               any(categorized_nodes.get('core5g_components', {}).values()))
        
        if has_docker_components:
            f.write('    \n')
            f.write('    # Setup Docker network\n')
            f.write('    info("*** Setting up Docker network\\n")\n')
            f.write('    create_docker_network_if_needed()\n')
            f.write('    \n')
        
        # Store network name for use in component creation
        if dynamic_network_name:
            f.write(f'    # Dynamic network mode based on topology file: {os.path.basename(self.main_window.current_file) if self.main_window.current_file else "Unknown"}\n')
            f.write(f'    NETWORK_MODE = "{dynamic_network_name}"\n')
            f.write(f'    info(f"*** Using Docker network: {{NETWORK_MODE}}\\n")\n')
        else:
            f.write(f'    # Default network mode when no file is loaded\n')
            f.write(f'    NETWORK_MODE = "open5gs-ueransim_default"\n')
            f.write(f'    info(f"*** Using default Docker network: {{NETWORK_MODE}}\\n")\n')
        f.write('    \n')
        
        # Create necessary directories
        f.write('    # Create config and logging directories if they don\'t exist\n')
        f.write('    os.makedirs(os.path.join(cwd, "config"), exist_ok=True)\n')
        f.write('    os.makedirs(os.path.join(cwd, "logging"), exist_ok=True)\n\n')
        
        # Add debug function
        f.write('    def debug_node_interfaces():\n')
        f.write('        """Debug function to check node interfaces"""\n')
        f.write('        print("\\n=== Node Interface Debug ===")\n')
        f.write('        for node in net.values():\n')
        f.write('            if hasattr(node, "name"):\n')
        f.write('                intfs = list(node.intfNames()) if hasattr(node, "intfNames") else []\n')
        f.write('                node_type = type(node).__name__\n')
        f.write('                print(f"{node.name} ({node_type}): {intfs}")\n')
        f.write('    \n')
        
        f.write('    def debug_network_mode():\n')
        f.write('        """Debug function to check network capabilities"""\n')
        f.write('        print("\\n=== Network Mode Debug ===")\n')
        f.write('        print(f"CONTAINERNET_AVAILABLE: {CONTAINERNET_AVAILABLE}")\n')
        f.write('        print(f"WIFI_AVAILABLE: {WIFI_AVAILABLE}")\n')
        f.write('        print(f"Network type: {type(net).__name__}")\n')
        f.write('        print(f"NETWORK_MODE: {NETWORK_MODE}")\n')
        f.write('    \n')
        
        # Initialize network
        self.write_network_initialization(f, categorized_nodes)
        
        # Add controllers
        self.write_controllers(f, categorized_nodes)
        
        # Add network components
        f.write('    info("*** Creating nodes\\n")\n')
        self.write_access_points(f, categorized_nodes)
        self.write_stations(f, categorized_nodes)
        self.write_hosts(f, categorized_nodes)
        self.write_switches(f, categorized_nodes)
        self.write_5g_components(f, categorized_nodes)
        self.write_docker_hosts(f, categorized_nodes)
        
        # Configure nodes
        f.write('    info("*** Configuring nodes\\n")\n')
        f.write('    # configureNodes() is only available in mininet-wifi\n')
        f.write('    if hasattr(net, "configureNodes"):\n')
        f.write('        net.configureNodes()\n')
        f.write('    else:\n')
        f.write('        # Standard Mininet doesn\'t need explicit node configuration\n')
        f.write('        pass\n\n')
        
        # Set propagation model if wireless components exist
        self.write_propagation_model(f, categorized_nodes)
        
        # Create links
        f.write('    info("*** Creating links\\n")\n')
        self.write_links(f, links, categorized_nodes)
        
        # Ensure all containers have at least one interface for Docker network connectivity
        f.write('    info("*** Ensuring container connectivity\\n")\n')
        self.write_container_connectivity(f, categorized_nodes)
        
        # Add default links for 5G components if no explicit links are defined
        has_5g_components = bool(categorized_nodes['gnbs'] or categorized_nodes['ues'] or categorized_nodes['core5g'])
        has_switches_or_aps = bool(categorized_nodes['aps'] or categorized_nodes['switches'])
        has_explicit_links = bool(links and len(links) > 0)
        
        f.write(f'    # Debug: has_5g_components={has_5g_components}, has_switches_or_aps={has_switches_or_aps}, links={len(links) if links else 0}\n')
        
        # Only create default switch if there are 5G components but NO switches/APs AND NO explicit links
        # This is more conservative - if user has defined links, respect their topology design
        should_create_default = (
            self.auto_create_default_switch and
            has_5g_components and 
            not has_switches_or_aps and 
            (not self.respect_explicit_topology or not has_explicit_links)
        )
        
        if should_create_default:
            f.write('    # Add default connectivity for 5G components (no explicit topology defined)\n')
            f.write('    print("*** Creating default switch for 5G component connectivity")\n')
            f.write('    default_switch = net.addSwitch("s1", cls=OVSKernelSwitch, protocols="OpenFlow14")\n')
            
            # Connect all 5G core components to the switch
            core_components = categorized_nodes.get('core5g_components', {})
            all_core_names = []
            for comp_type, components in core_components.items():
                for component in components:
                    comp_name = self.sanitize_variable_name(component.get('name', f'{comp_type.lower()}1'))
                    all_core_names.append(comp_name)
            
            for comp_name in all_core_names:
                f.write(f'    try:\n')
                f.write(f'        net.addLink(default_switch, {comp_name})\n')
                f.write(f'        print(f"*** Connected {{default_switch.name}} to {comp_name}")\n')
                f.write(f'    except Exception as e:\n')
                f.write(f'        print(f"*** Warning: Failed to connect {comp_name}: {{e}}")\n')
            
            # Connect gNBs to the switch
            for gnb in categorized_nodes['gnbs']:
                gnb_name = self.sanitize_variable_name(gnb['name'])
                f.write(f'    try:\n')
                f.write(f'        net.addLink(default_switch, {gnb_name})\n')
                f.write(f'        print(f"*** Connected {{default_switch.name}} to {gnb_name}")\n')
                f.write(f'    except Exception as e:\n')
                f.write(f'        print(f"*** Warning: Failed to connect {gnb_name}: {{e}}")\n')
            
            # Connect UEs to the switch  
            for ue in categorized_nodes['ues']:
                ue_name = self.sanitize_variable_name(ue['name'])
                f.write(f'    try:\n')
                f.write(f'        net.addLink(default_switch, {ue_name})\n')
                f.write(f'        print(f"*** Connected {{default_switch.name}} to {ue_name}")\n')
                f.write(f'    except Exception as e:\n')
                f.write(f'        print(f"*** Warning: Failed to connect {ue_name}: {{e}}")\n')
            f.write('\n')
        
        # Add plot for wireless networks
        self.write_plot_graph(f, categorized_nodes)
        
        # Start network
        f.write('    info("*** Starting network\\n")\n')
        f.write('    net.build()\n')
        f.write('    \n')
        f.write('    # Debug: Check network mode and node interfaces after build\n')
        f.write('    debug_network_mode()\n')
        f.write('    debug_node_interfaces()\n')
        f.write('    \n')
        self.write_controller_startup(f, categorized_nodes)
        self.write_ap_startup(f, categorized_nodes)
        
        # Start 5G components (without rebuilding network)
        self.write_5g_startup(f, categorized_nodes)
        
        # CLI and cleanup
        f.write('    info("*** Running CLI\\n")\n')
        f.write('    CLI(net)\n\n')
        f.write('    info("*** Stopping network\\n")\n')
        f.write('    net.stop()\n\n')

    def write_network_initialization(self, f, categorized_nodes):
        """Write network initialization code following fixed_topology-upf.py pattern."""
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        has_docker = (categorized_nodes['docker_hosts'] or categorized_nodes['ues'] or 
                     categorized_nodes['gnbs'] or categorized_nodes['core5g'])
        
        # Priority: Containernet > Mininet-wifi > Standard Mininet
        if has_docker:
            f.write('    # Use containernet for Docker support, with fallbacks\n')
            f.write('    if CONTAINERNET_AVAILABLE:\n')
            f.write('        net = Containernet(topo=None, build=False, ipBase=\'10.0.0.0/8\')\n')
            f.write('    elif WIFI_AVAILABLE:\n')
            f.write('        net = Mininet_wifi(topo=None,\n')
            f.write('                           build=False,\n')
            f.write('                           link=wmediumd, wmediumd_mode=interference,\n')
            f.write('                           ipBase=\'10.0.0.0/8\')\n')
            f.write('    else:\n')
            f.write('        print("Using standard Mininet (containernet and mininet-wifi not available)")\n')
            f.write('        net = Mininet(topo=None, build=False, ipBase=\'10.0.0.0/8\')\n')
        elif has_wireless:
            f.write('    # Use mininet-wifi if available, otherwise fallback to standard Mininet\n')
            f.write('    if WIFI_AVAILABLE:\n')
            f.write('        net = Mininet_wifi(topo=None,\n')
            f.write('                           build=False,\n')
            f.write('                           link=wmediumd, wmediumd_mode=interference,\n')
            f.write('                           ipBase=\'10.0.0.0/8\')\n')
            f.write('    else:\n')
            f.write('        print("Using standard Mininet (mininet-wifi not available)")\n')
            f.write('        net = Mininet(topo=None, build=False, ipBase=\'10.0.0.0/8\')\n')
        else:
            f.write('    net = Mininet(topo=None, build=False, ipBase=\'10.0.0.0/8\')\n')
        f.write('\n')

    def write_controllers(self, f, categorized_nodes):
        """Write controller creation code following fixed_topology-upf.py pattern."""
        f.write('    info("*** Adding controller\\n")\n')
        if categorized_nodes['controllers']:
            for controller in categorized_nodes['controllers']:
                props = controller.get('properties', {})
                ctrl_name = self.sanitize_variable_name(controller['name'])
                ctrl_ip = props.get('Controller_IPAddress', '127.0.0.1')
                ctrl_port = props.get('Controller_Port', 6633)
                
                f.write(f'    {ctrl_name} = net.addController(name=\'{ctrl_name}\',\n')
                f.write(f'                                   controller=RemoteController,\n')
                f.write(f'                                   ip=\'{ctrl_ip}\',\n')
                f.write(f'                                   port={ctrl_port})\n')
        else:
            # Add default controller like in the original
            f.write('    c0 = net.addController(name=\'c0\',\n')
            f.write('                           controller=RemoteController)\n')
        f.write('\n')

    def write_access_points(self, f, categorized_nodes):
        """Write Access Point creation code following fixed_topology-upf.py pattern."""
        if not categorized_nodes['aps']:
            return
            
        f.write('    info("*** Add APs & Switches\\n")\n')
        for ap in categorized_nodes['aps']:
            props = ap.get('properties', {})
            ap_name = self.sanitize_variable_name(ap['name'])
            
            # Extract properties from UI
            ssid = props.get('AP_SSID', props.get('lineEdit_5', f'{ap_name}-ssid'))
            channel = props.get('AP_Channel', props.get('spinBox_2', '36'))
            mode = props.get('AP_Mode', props.get('comboBox_2', 'a'))
            position = f"{ap.get('x', 0):.1f},{ap.get('y', 0):.1f},0"
            
            # Build AP parameters following the original pattern
            ap_params = [f"'{ap_name}'"]
            ap_params.append("cls=OVSKernelAP")
            ap_params.append(f"ssid='{ssid}'")
            ap_params.append("failMode='standalone'")
            ap_params.append("datapath='user'")
            ap_params.append(f"channel='{channel}'")
            ap_params.append(f"mode='{mode}'")
            ap_params.append(f"position='{position}'")
            
            # Add power configuration for radio propagation
            from manager.configmap import ConfigurationMapper
            ap_config_opts = ConfigurationMapper.map_ap_config(props)
            for opt in ap_config_opts:
                if 'txpower=' in opt or 'range=' in opt:
                    ap_params.append(opt)
            
            ap_params.append('protocols="OpenFlow14"')
            
            f.write(f'    {ap_name} = net.addAccessPoint({", ".join(ap_params)})\n')
        f.write('\n')

    def write_stations(self, f, categorized_nodes):
        """Write Station creation code with dynamic properties."""
        if not categorized_nodes['stas']:
            return
            
        for sta in categorized_nodes['stas']:
            props = sta.get('properties', {})
            sta_name = self.sanitize_variable_name(sta['name'])
            
            # Build station parameters using ConfigurationMapper
            sta_params = [f"'{sta_name}'"]
            
            # Add position
            position = f"{sta.get('x', 0):.1f},{sta.get('y', 0):.1f},0"
            sta_params.append(f"position='{position}'")
            
            # Add configuration options from ConfigurationMapper
            from manager.configmap import ConfigurationMapper
            sta_opts = ConfigurationMapper.map_sta_config(props)
            sta_params.extend(sta_opts)
            
            f.write(f'    {sta_name} = add_node_to_network(net, {", ".join(sta_params)})\n')
        f.write('\n')

    def write_hosts(self, f, categorized_nodes):
        """Write Host creation code with dynamic properties."""
        if not categorized_nodes['hosts']:
            return
            
        for host in categorized_nodes['hosts']:
            props = host.get('properties', {})
            host_name = self.sanitize_variable_name(host['name'])
            
            # Build host parameters
            host_params = [f"'{host_name}'"]
            
            # Add IP if specified
            ip_addr = props.get('Host_IPAddress', props.get('lineEdit_2'))
            if ip_addr and str(ip_addr).strip() and str(ip_addr).strip() != "192.168.1.1":
                host_params.append(f"ip='{ip_addr}'")
            
            # Add MAC if specified
            mac_addr = props.get('Host_MACAddress', props.get('lineEdit'))
            if mac_addr and str(mac_addr).strip():
                host_params.append(f"mac='{mac_addr}'")
            
            # Add CPU if specified
            cpu = props.get('Host_AmountCPU', props.get('doubleSpinBox'))
            if cpu and float(cpu) != 1.0:
                host_params.append(f"cpu={cpu}")
            
            # Add memory if specified
            memory = props.get('Host_Memory', props.get('spinBox'))
            if memory and int(memory) > 0:
                host_params.append(f"mem={memory}")
            
            f.write(f'    {host_name} = net.addHost({", ".join(host_params)})\n')
        f.write('\n')

    def write_switches(self, f, categorized_nodes):
        """Write Switch creation code following fixed_topology-upf.py pattern."""
        if not categorized_nodes['switches']:
            return
            
        # Add switches to the same section as APs (continued from write_access_points)
        for i, switch in enumerate(categorized_nodes['switches'], 1):
            props = switch.get('properties', {})
            switch_name = self.sanitize_variable_name(switch['name'])
            
            # Build switch parameters following the original pattern
            switch_params = [f"'{switch_name}'"]
            switch_params.append("cls=OVSKernelSwitch")
            switch_params.append('protocols="OpenFlow14"')
            
            # Add DPID if specified
            dpid = props.get('Switch_DPID', props.get('Router_DPID', props.get('AP_DPID', props.get('lineEdit_4'))))
            if dpid and str(dpid).strip():
                switch_params.append(f"dpid='{dpid}'")
            
            f.write(f'    {switch_name} = net.addSwitch({", ".join(switch_params)})\n')
        f.write('\n')

    def write_docker_hosts(self, f, categorized_nodes):
        """Write Docker Host creation code with dynamic properties."""
        if not categorized_nodes['docker_hosts']:
            return
            
        for docker_host in categorized_nodes['docker_hosts']:
            props = docker_host.get('properties', {})
            host_name = self.sanitize_variable_name(docker_host['name'])
            
            # Build Docker host parameters
            host_params = [f"'{host_name}'"]
            host_params.append("cls=Docker")
            
            # Add Docker image if specified
            image = props.get('DockerHost_ContainerImage', props.get('lineEdit_10'))
            if image and str(image).strip():
                host_params.append(f"dimage='{image}'")
            
            # Add port forwarding if specified
            ports = props.get('DockerHost_PortForward', props.get('lineEdit_11'))
            if ports and str(ports).strip():
                host_params.append(f"ports='{ports}'")
            
            # Add volume mapping if specified
            volumes = props.get('DockerHost_VolumeMapping', props.get('lineEdit_12'))
            if volumes and str(volumes).strip():
                host_params.append(f"volumes='{volumes}'")
            
            # Add IP if specified
            ip_addr = props.get('DockerHost_IPAddress', props.get('lineEdit_2'))
            if ip_addr and str(ip_addr).strip() and str(ip_addr).strip() != "192.168.1.1":
                host_params.append(f"ip='{ip_addr}'")
            
            # Add MAC if specified
            mac_addr = props.get('DockerHost_MACAddress', props.get('lineEdit'))
            if mac_addr and str(mac_addr).strip():
                host_params.append(f"mac='{mac_addr}'")
            
            # Add CPU if specified
            cpu = props.get('DockerHost_AmountCPU', props.get('doubleSpinBox'))
            if cpu and float(cpu) != 1.0:
                host_params.append(f"cpu={cpu}")
            
            # Add memory if specified
            memory = props.get('DockerHost_Memory', props.get('spinBox'))
            if memory and int(memory) > 0:
                host_params.append(f"mem={memory}")
            
            f.write(f'    {host_name} = net.addHost({", ".join(host_params)})\n')
        f.write('\n')

    def write_aps_and_switches_level2(self, f, categorized_nodes):
        """Write APs and switches with Level 2 hierarchical topology features."""
        if categorized_nodes['aps'] or categorized_nodes['switches']:
            f.write('    info( \'\\n*** Add APs & Switches\\n\')\n')
            
            # Add APs with enhanced configuration
            for i, ap in enumerate(categorized_nodes['aps'], 1):
                props = ap.get('properties', {})
                ap_name = self.sanitize_variable_name(ap['name'])
                ssid = props.get('AP_SSID', f'{ap_name}-ssid')
                channel = props.get('AP_Channel', '36')
                mode = props.get('AP_Mode', 'a')
                
                # Build AP parameters
                ap_params = [f"'{ap_name}'"]
                ap_params.append(f"ssid='{ssid}'")
                ap_params.append(f"mode='{mode}'")
                ap_params.append(f"channel='{channel}'")
                
                # Hierarchical position: level2-apX
                ap_params.append(f"position='0,0,{i}'")
                ap_params.append("failMode='standalone'")
                
                f.write(f'    {ap_name} = net.addAccessPoint({", ".join(ap_params)})\n')
            
            # Add switches
            for i, switch in enumerate(categorized_nodes['switches'], 1):
                props = switch.get('properties', {})
                switch_name = self.sanitize_variable_name(switch['name'])
                
                # Build switch parameters
                switch_params = [f"'{switch_name}'"]
                switch_params.append("cls=OVSKernelSwitch")
                
                # Add DPID if specified
                dpid = props.get('Switch_DPID', props.get('Router_DPID', props.get('AP_DPID', props.get('lineEdit_4'))))
                if dpid and str(dpid).strip():
                    switch_params.append(f"dpid='{dpid}'")
                
                # Hierarchical position: level2-switchX
                switch_params.append(f"position='0,0,{i+len(categorized_nodes['aps'])}'")
                
                f.write(f'    {switch_name} = net.addSwitch({", ".join(switch_params)})\n')
            
            f.write('\n')

    def write_5g_components(self, f, categorized_nodes):
        """Write 5G component creation code (gNBs and UEs) with enhanced AP functionality."""
        # Write 5G Core components first
        self.write_5g_core_components(f, categorized_nodes)
        
        # Write gNBs following the enhanced pattern with AP support
        if categorized_nodes['gnbs']:
            f.write('    info("*** Add gNB\\n")\n')
            
            # Check for required Docker images before creating gNBs
            f.write('    # Check for required Docker images\n')
            f.write('    # Use locally built UERANSIM image first\n')
            f.write('    ueransim_image = "adaptive/ueransim:latest"\n')
            f.write('    if CONTAINERNET_AVAILABLE and not check_docker_image(ueransim_image):\n')
            f.write('        print("*** Warning: Free5GMANO UERANSIM image not available. Trying alternative images...")\n')
            f.write('        # Try alternative image names\n')
            f.write('        # Try other alternative images if locally built one fails\n')
            f.write('        alternative_images = ["free5gmano/ueransim:latest", "ueransim:latest", "open5gs/ueransim:latest", "ghcr.io/aligungr/ueransim:latest"]\n')
            f.write('        ueransim_image_found = False\n')
            f.write('        for alt_image in alternative_images:\n')
            f.write('            if check_docker_image(alt_image):\n')
            f.write('                ueransim_image = alt_image\n')
            f.write('                ueransim_image_found = True\n')
            f.write('                print(f"*** Using alternative image: {alt_image}")\n')
            f.write('                break\n')
            f.write('        if not ueransim_image_found:\n')
            f.write('            print("*** Error: No suitable UERANSIM image found!")\n')
            f.write('            print("*** Please ensure UERANSIM Docker image is available:")\n')
            f.write('            print("***   docker build -t adaptive/ueransim:latest . (from UERANSIM directory)")\n')
            f.write('            print("*** Or pull from registry: docker pull free5gmano/ueransim:latest")\n')
            f.write('            print("*** Skipping gNB creation...")\n')
            f.write('    else:\n')
            f.write('        ueransim_image_found = True\n')
            f.write('    \n')
            f.write('    if ueransim_image_found or not CONTAINERNET_AVAILABLE:\n')
            
            for i, gnb in enumerate(categorized_nodes['gnbs'], 1):
                props = gnb.get('properties', {})
                gnb_name = self.sanitize_variable_name(gnb['name'])
                
                # Build gNB parameters following the enhanced pattern
                f.write(f'        # Build gNB parameters\n')
                f.write(f'        gnb_kwargs = {{}}\n')
                f.write(f'        if CONTAINERNET_AVAILABLE:\n')
                f.write(f'            gnb_kwargs.update({{\n')
                f.write(f'                "dimage": ueransim_image,\n')
                f.write(f'                "dcmd": "/bin/bash",\n')
                f.write(f'                "cap_add": ["net_admin"],\n')
                f.write(f'                "network_mode": NETWORK_MODE,\n')
                f.write(f'                "publish_all_ports": True,\n')
                f.write(f'                "privileged": True,\n')
                
                # Add volumes for host hardware access (needed for AP functionality)
                volumes = [
                    '"/sys:/sys"',
                    '"/lib/modules:/lib/modules"',
                    '"/sys/kernel/debug:/sys/kernel/debug"',
                    'cwd + "/config:/config"',
                    'cwd + "/logging:/logging"'
                ]
                f.write(f'                "volumes": [{", ".join(volumes)}],\n')
                
                # Get enhanced configuration from ConfigurationMapper
                from manager.configmap import ConfigurationMapper
                gnb_config = ConfigurationMapper.map_gnb_config(props)
                
                # Build environment variables for both 5G and AP functionality
                env_dict = {}
                
                # 5G Core configuration
                env_dict["AMF_IP"] = gnb_config.get('amf_hostname', '10.0.0.3')  # Note: Still using IP for compatibility
                env_dict["GNB_HOSTNAME"] = gnb_config.get('gnb_hostname', f'mn.{gnb_name}')
                env_dict["N2_IFACE"] = gnb_config.get('n2_iface', f"{gnb_name}-wlan0")
                env_dict["N3_IFACE"] = gnb_config.get('n3_iface', f"{gnb_name}-wlan0")
                env_dict["RADIO_IFACE"] = gnb_config.get('radio_iface', f"{gnb_name}-wlan0")
                env_dict["MCC"] = gnb_config.get('mcc', '999')
                env_dict["MNC"] = gnb_config.get('mnc', '70')
                env_dict["SST"] = gnb_config.get('sst', '1')
                env_dict["SD"] = gnb_config.get('sd', '0xffffff')
                env_dict["TAC"] = gnb_config.get('tac', '1')
                
                # Add AP configuration if enabled
                ap_config = gnb_config.get('ap_config', {})
                if ap_config:
                    env_dict.update(ap_config)
                
                # Format environment like in the original
                env_str = str(env_dict).replace("'", '"')
                f.write(f'                "environment": {env_str}\n')
                f.write(f'            }})\n')
                f.write(f'        elif WIFI_AVAILABLE:\n')
                f.write(f'            # mininet-wifi parameters\n')
                f.write(f'            gnb_kwargs.update({{\n')
                
                # Add position
                position = f"{gnb.get('x', 0):.1f},{gnb.get('y', 0):.1f},0"
                f.write(f'                "position": "{position}",\n')
                
                # Add range (default 300 if not specified)
                range_val = gnb_config.get('range', 300)
                f.write(f'                "range": {range_val},\n')
                
                # Add txpower if specified (default 30)
                txpower = gnb_config.get('txpower', 30)
                f.write(f'                "txpower": {txpower}\n')
                f.write(f'            }})\n')
                f.write(f'        else:\n')
                f.write(f'            # Standard Mininet parameters\n')
                f.write(f'            gnb_kwargs.update({{\n')
                f.write(f'                "cls": Host\n')
                f.write(f'            }})\n')
                
                f.write(f'        {gnb_name} = add_node_to_network(net, \'{gnb_name}\', **gnb_kwargs)\n')
            f.write('\n')
        
        # Write UEs following the exact pattern from fixed_topology-upf.py
        if categorized_nodes['ues']:
            f.write('    info("*** Adding docker UE hosts\\n")\n')
            
            # Check for required UE Docker images
            f.write('    # Check for required UE Docker images\n')
            f.write('    # Use locally built UERANSIM image for UE components\n')
            f.write('    ue_image = "adaptive/ueransim:latest"\n')
            f.write('    if CONTAINERNET_AVAILABLE and not check_docker_image(ue_image):\n')
            f.write('        print("*** Warning: Gradiant UERANSIM UE image not available. Trying alternatives...")\n')
            f.write('        # Try alternative UE image names\n')
            f.write('        # Try other alternative images if locally built one fails\n')
            f.write('        ue_alternatives = ["gradiant/ueransim:3.2.6", "free5gmano/ueransim:latest", "ueransim:latest", "open5gs/ueransim:latest"]\n')
            f.write('        ue_image_found = False\n')
            f.write('        for alt_image in ue_alternatives:\n')
            f.write('            if check_docker_image(alt_image):\n')
            f.write('                ue_image = alt_image\n')
            f.write('                ue_image_found = True\n')
            f.write('                print(f"*** Using alternative UE image: {alt_image}")\n')
            f.write('                break\n')
            f.write('        if not ue_image_found:\n')
            f.write('            print("*** Error: No suitable UERANSIM UE image found!")\n')
            f.write('            print("*** Please ensure UERANSIM UE Docker image is available:")\n')
            f.write('            print("***   docker build -t adaptive/ueransim:latest . (from UERANSIM directory)")\n')
            f.write('            print("*** Or pull from registry: docker pull gradiant/ueransim:3.2.6")\n')
            f.write('            print("*** Skipping UE creation...")\n')
            f.write('    else:\n')
            f.write('        ue_image_found = True\n')
            f.write('    \n')
            f.write('    if ue_image_found or not CONTAINERNET_AVAILABLE:\n')
            
            for i, ue in enumerate(categorized_nodes['ues'], 1):
                props = ue.get('properties', {})
                ue_name = self.sanitize_variable_name(ue['name'])
                
                # Build UE parameters following the exact pattern
                f.write(f'        # Build UE parameters\n')
                f.write(f'        ue_kwargs = {{}}\n')
                f.write(f'        if CONTAINERNET_AVAILABLE:\n')
                f.write(f'            ue_kwargs.update({{\n')
                f.write(f'                "dimage": ue_image,\n')
                f.write(f'                "dcmd": "/bin/bash",\n')
                f.write(f'                "devices": ["/dev/net/tun"],\n')
                f.write(f'                "cap_add": ["net_admin"],\n')
                f.write(f'                "network_mode": NETWORK_MODE,\n')
                f.write(f'                "volumes": [cwd + "/config:/config", cwd + "/logging:/logging"],\n')
                
                # Add enhanced power and range configuration from ConfigurationMapper
                from manager.configmap import ConfigurationMapper
                ue_config = ConfigurationMapper.map_ue_config(props)
                
                # Enhanced UE environment variables with all new configuration options
                gnb_hostname = ue_config.get('gnb_hostname', 'mn.gnb')
                
                # Build comprehensive environment dictionary
                env_dict = {
                    # Core 5G Configuration
                    "GNB_HOSTNAME": gnb_hostname,
                    "APN": ue_config.get('apn', 'internet'),
                    "MSISDN": ue_config.get('msisdn', f'000000000{i:01d}'),
                    "MCC": ue_config.get('mcc', '999'),
                    "MNC": ue_config.get('mnc', '70'),
                    "SST": ue_config.get('sst', '1'),
                    "SD": ue_config.get('sd', '0xffffff'),
                    "TAC": ue_config.get('tac', '1'),
                    
                    # Authentication Configuration
                    "KEY": ue_config.get('key', '465B5CE8B199B49FAA5F0A2EE238A6BC'),
                    "OP_TYPE": ue_config.get('op_type', 'OPC'),
                    "OP": ue_config.get('op', 'E8ED289DEBA952E4283B54E88E6183CA'),
                    
                    # Device Identifiers
                    "IMEI": ue_config.get('imei', '356938035643803'),
                    "IMEISV": ue_config.get('imeisv', '4370816125816151'),
                    
                    # Network Configuration
                    "TUNNEL_IFACE": ue_config.get('tunnel_iface', 'uesimtun0'),
                    "RADIO_IFACE": ue_config.get('radio_iface', 'eth0'),
                    "SESSION_TYPE": ue_config.get('session_type', 'IPv4'),
                    "PDU_SESSIONS": str(ue_config.get('pdu_sessions', 1)),
                    
                    # Mobility Configuration
                    "MOBILITY_ENABLED": 'true' if ue_config.get('mobility', False) else 'false'
                }
                
                # Add gNB IP if specified
                if 'gnb_ip' in ue_config:
                    env_dict["GNB_IP"] = ue_config['gnb_ip']
                
                # Format environment like in the original
                env_str = str(env_dict).replace("'", '"')
                f.write(f'                "environment": {env_str}\n')
                f.write(f'            }})\n')
                f.write(f'        elif WIFI_AVAILABLE:\n')
                f.write(f'            # mininet-wifi parameters\n')
                f.write(f'            ue_kwargs.update({{\n')
                
                # Add range (default 116 if not specified)
                range_val = ue_config.get('range', 116)
                f.write(f'                "range": {range_val},\n')
                
                # Add txpower if specified
                if 'txpower' in ue_config:
                    f.write(f'                "txpower": {ue_config["txpower"]},\n')
                
                # Add association mode if specified
                if 'association' in ue_config and ue_config['association'] != 'auto':
                    f.write(f'                "associationMode": "{ue_config["association"]}",\n')
                
                # Add position
                position = f"{ue.get('x', 0):.1f},{ue.get('y', 0):.1f},0"
                f.write(f'                "position": "{position}"\n')
                f.write(f'            }})\n')
                f.write(f'        else:\n')
                f.write(f'            # Standard Mininet parameters\n')
                f.write(f'            ue_kwargs.update({{\n')
                f.write(f'                "cls": Host\n')
                f.write(f'            }})\n')
                
                f.write(f'        {ue_name} = add_node_to_network(net, \'{ue_name}\', **ue_kwargs)\n')
            f.write('\n')
        
        if categorized_nodes['gnbs'] or categorized_nodes['ues'] or categorized_nodes['core5g']:
            f.write('\n')

    def write_5g_core_components(self, f, categorized_nodes):
        """
        Write 5G Core components with enhanced Open5GS integration and dynamic configuration.
        
        This function generates Docker-based 5G Core components that follow the latest Open5GS
        architecture and container configuration. Features include:
        
        - Dynamic Docker image configuration from UI
        - Environment variable injection for runtime configuration
        - Support for latest Open5GS component structure
        - OVS/OpenFlow integration for SDN functionality
        - Proper network interface binding
        - MongoDB database connectivity
        - Configuration file volume mounting
        - Component-specific startup commands
        
        The generated components are compatible with mininet-wifi and follow the
        patterns established in the latest Open5GS Docker implementations.
        """
        if not categorized_nodes['core5g']:
            return
            
        # Extract 5G core components from VGcore configurations
        core_components = self.extract_5g_components_by_type(categorized_nodes['core5g'])
        
        # Import configuration mapper for VGcore properties
        from manager.configmap import ConfigurationMapper
        
        # Get VGcore component configuration (if available)
        vgcore_config = {}
        if categorized_nodes['core5g']:
            vgcore_node = categorized_nodes['core5g'][0]  # Use first VGcore node
            vgcore_properties = vgcore_node.get('properties', {})
            vgcore_config = ConfigurationMapper.map_vgcore_config(vgcore_properties)
        
        # Debug: Print extracted VGcore configuration for troubleshooting
        if vgcore_config:
            debug_print("DEBUG: VGcore configuration extracted:")
            for key, value in vgcore_config.items():
                debug_print(f"  {key}: {value}")
        else:
            debug_print("DEBUG: No VGcore configuration found, using defaults")
        
        # Mapping of component types to their configurations based on latest Open5GS
        component_config = {
            'UPF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'upf.yaml',
                'startup_cmd': 'open5gs-upfd',
                'privileged': True,
                'requires_tun': False,
                'terminal_startup': True,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'ENABLE_NAT': 'true' if vgcore_config.get('enable_nat', True) else 'false',
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0'),
                    'OVS_ENABLED': 'true' if vgcore_config.get('ovs_enabled', False) else 'false',
                    'OVS_CONTROLLER': vgcore_config.get('ovs_controller', ''),
                    'OVS_BRIDGE_NAME': vgcore_config.get('ovs_bridge_name', 'br-open5gs'),
                    'OVS_FAIL_MODE': vgcore_config.get('ovs_fail_mode', 'standalone'),
                    'OPENFLOW_PROTOCOLS': vgcore_config.get('openflow_protocols', 'OpenFlow14'),
                    'OVS_DATAPATH': vgcore_config.get('ovs_datapath', 'kernel'),
                    'CONTROLLER_PORT': vgcore_config.get('controller_port', '6633'),
                    'BRIDGE_PRIORITY': vgcore_config.get('bridge_priority', '32768'),
                    'STP_ENABLED': 'true' if vgcore_config.get('stp_enabled', False) else 'false'
                }
            },
            'AMF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'amf.yaml',
                'startup_cmd': 'open5gs-amfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': True,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0'),
                    'MCC': vgcore_config.get('mcc', '999'),
                    'MNC': vgcore_config.get('mnc', '70'),
                    'TAC': vgcore_config.get('tac', '1'),
                    'SST': vgcore_config.get('sst', '1'),
                    'SD': vgcore_config.get('sd', '0xffffff')
                }
            },
            'SMF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'smf.yaml',
                'startup_cmd': 'open5gs-smfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'NRF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'nrf.yaml',
                'startup_cmd': 'open5gs-nrfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'SCP': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'scp.yaml',
                'startup_cmd': 'open5gs-scpd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'AUSF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'ausf.yaml',
                'startup_cmd': 'open5gs-ausfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'BSF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'bsf.yaml',
                'startup_cmd': 'open5gs-bsfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'NSSF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'nssf.yaml',
                'startup_cmd': 'open5gs-nssfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'PCF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'pcf.yaml',
                'startup_cmd': 'open5gs-pcfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'UDM': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'udm.yaml',
                'startup_cmd': 'open5gs-udmd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'UDR': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:1.0'),
                'default_config': 'udr.yaml',
                'startup_cmd': 'open5gs-udrd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            }
        }
        
        # Generate code for each 5G core component type
        for comp_type, components in core_components.items():
            if components:
                config = component_config.get(comp_type, component_config['AMF'])
                f.write(f'    info("*** Add {comp_type}\\n")\n')
                
                for i, component in enumerate(components, 1):
                    comp_name = self.sanitize_variable_name(component.get('name', f'{comp_type.lower()}1'))
                    
                    # Build component parameters following fixed_topology-upf.py pattern
                    f.write(f'    # Build {comp_type} parameters\n')
                    f.write(f'    comp_kwargs = {{}}\n')
                    f.write(f'    if CONTAINERNET_AVAILABLE:\n')
                    f.write(f'        comp_kwargs.update({{\n')
                    
                    # Add required Docker parameters
                    if config['requires_tun']:
                        f.write(f'            "devices": ["/dev/net/tun"],\n')
                    f.write(f'            "cap_add": ["net_admin"],\n')
                    f.write(f'            "network_mode": NETWORK_MODE,\n')
                    
                    if config['privileged']:
                        f.write(f'            "privileged": True,\n')
                    
                    f.write(f'            "publish_all_ports": True,\n')
                    f.write(f'            "dcmd": "/bin/bash",\n')
                    f.write(f'            "dimage": "{config["image"]}",\n')
                    
                    # Add position
                    x_pos = component.get('x', 0)
                    y_pos = component.get('y', 0)
                    position = f"{x_pos:.1f},{y_pos:.1f},0"
                    f.write(f'            "position": "{position}",\n')
                    f.write(f'            "range": 116,\n')
                    
                    # Add volume mount for configuration
                    config_file = component.get('config_file', config['default_config'])
                    f.write(f'            "volumes": [cwd + "/config/{config_file}:/opt/open5gs/etc/open5gs/{comp_type.lower()}.yaml"],\n')
                    
                    # Add environment variables for configuration
                    if 'env_vars' in config and config['env_vars']:
                        env_list = []
                        for env_key, env_value in config['env_vars'].items():
                            env_list.append(f'"{env_key}={env_value}"')
                        if env_list:
                            f.write(f'            "environment": [{", ".join(env_list)}]\n')
                    
                    f.write(f'        }})\n')
                    f.write(f'    else:\n')
                    f.write(f'        # Standard Mininet parameters\n')
                    f.write(f'        comp_kwargs.update({{\n')
                    f.write(f'            "cls": Host,\n')
                    f.write(f'            "position": "{position}"\n')
                    f.write(f'        }})\n')
                    
                    f.write(f'    {comp_name} = add_node_to_network(net, \'{comp_name}\', **comp_kwargs)\n')
        
        f.write('\n')

    def write_5g_startup(self, f, categorized_nodes):
        """Write 5G component startup commands following fixed_topology-upf.py pattern."""
        if not (categorized_nodes['gnbs'] or categorized_nodes['ues'] or categorized_nodes['core5g']):
            return
            
        # Get core components for startup sequence
        core_components = categorized_nodes.get('core5g_components', {})
        
        # Add capture script execution like in original
        f.write('    info("*** Capture all initialization flow and slice packet\\n")\n')
        f.write('    Capture1 = cwd + "/capture-initialization-fixed.sh"\n')
        f.write('    # Check if capture script exists and run it properly\n')
        f.write('    if os.path.exists(Capture1):\n')
        f.write('        try:\n')
        f.write('            with open(Capture1, "r") as script_file:\n')
        f.write('                CLI(net, script=script_file)\n')
        f.write('        except Exception as e:\n')
        f.write('            print(f"Warning: Error running capture script: {e}")\n')
        f.write('            CLI(net)\n')
        f.write('    else:\n')
        f.write('        print(f"Warning: Capture script not found: {Capture1}")\n')
        f.write('        CLI(net)\n\n')

        f.write('    CLI.do_sh(net, "sleep 20")\n\n')

        f.write('    info("*** pingall for testing and flow tables update\\n")\n')
        f.write('    net.pingAll()\n\n')
        
        f.write('    CLI.do_sh(net, "sleep 10")\n\n')
        
        # Start 5G Core components in proper order with makeTerm2
        startup_order = ['NRF', 'SCP', 'AUSF', 'UDM', 'UDR', 'PCF', 'BSF', 'NSSF', 'SMF']
        
        # Start UPF components first (they need special handling)
        if 'UPF' in core_components:
            f.write('    info("*** Post configure Docker UPF connection to Core\\n")\n')
            for instance in core_components['UPF']:
                instance_name = self.sanitize_variable_name(instance.get('name', 'upf1'))
                f.write(f'    makeTerm2({instance_name}, cmd="/entrypoint.sh open5gs-upfd 2>&1 | tee -a /logging/{instance_name}.log")\n')
            f.write('\n')
        
        # Start AMF components
        if 'AMF' in core_components:
            f.write('    info("*** Post configure Docker AMF connection to Core\\n")\n')
            for instance in core_components['AMF']:
                instance_name = self.sanitize_variable_name(instance.get('name', 'amf1'))
                f.write(f'    makeTerm2({instance_name}, cmd="open5gs-amfd 2>&1 | tee -a /logging/{instance_name}.log")\n')
            f.write('\n')
        
        # Start other core components (if configured)
        for comp_type in startup_order:
            if comp_type in core_components:
                f.write(f'    info("*** Starting {comp_type} components\\n")\n')
                for instance in core_components[comp_type]:
                    instance_name = self.sanitize_variable_name(instance.get('name', f'{comp_type.lower()}1'))
                    cmd = f'open5gs-{comp_type.lower()}d'
                    f.write(f'    makeTerm2({instance_name}, cmd="{cmd} 2>&1 | tee -a /logging/{instance_name}.log")\n')
                f.write('\n')
        
        f.write('    CLI.do_sh(net, "sleep 10")\n\n')
        
        # Start gNBs
        if categorized_nodes['gnbs']:
            f.write('    info("*** Post configure Docker gNB connection to AMF\\n")\n')
            
            # First, update gNB configurations with actual AMF IP addresses
            core_components = categorized_nodes.get('core5g_components', {})
            if 'AMF' in core_components and core_components['AMF']:
                f.write('    # Update gNB configurations with actual AMF IP addresses\n')
                amf_instance = core_components['AMF'][0]  # Use first AMF
                amf_name = self.sanitize_variable_name(amf_instance.get('name', 'amf1'))
                f.write(f'    amf_ip = {amf_name}.IP()\n')
                f.write(f'    print(f"AMF {amf_name} IP: {{amf_ip}}")\n')
                
                # Update all gNB config files with this AMF IP
                for gnb in categorized_nodes['gnbs']:
                    gnb_name = self.sanitize_variable_name(gnb['name'])
                    config_file = f"{gnb_name}.yaml"
                    # Replace placeholder with actual AMF IP
                    f.write(f'    result = {gnb_name}.cmd(f"sed -i \\"s/AMF_CONTAINER_IP_PLACEHOLDER/${{amf_ip}}/g\\" /config/{config_file}")\n')
                    # Also replace any hardcoded AMF IPs
                    f.write(f'    result = {gnb_name}.cmd(f"sed -i \\"s/172.18.0.10/${{amf_ip}}/g\\" /config/{config_file}")\n')
                    f.write(f'    print(f"Updated {gnb_name} config with AMF IP: {{amf_ip}}")\n')
                f.write('\n')
            
            for gnb in categorized_nodes['gnbs']:
                gnb_name = self.sanitize_variable_name(gnb['name'])
                # Use specific gNB configuration file for each gNB
                config_file = f"{gnb_name}.yaml"
                f.write(f'    makeTerm2({gnb_name}, cmd="/entrypoint.sh gnb /config/{config_file} 2>&1 | tee -a /logging/{gnb_name}.log")\n')
            f.write('\n')
            f.write('    CLI.do_sh(net, "sleep 10")\n\n')
        
        # Start UEs
        if categorized_nodes['ues']:
            f.write('    info("*** Post configure Docker UE nodes\\n")\n')
            
            # First, update UE configurations with actual gNB IP addresses
            if categorized_nodes['gnbs']:
                f.write('    # Update UE configurations with actual gNB IP addresses\n')
                for gnb in categorized_nodes['gnbs']:
                    gnb_name = self.sanitize_variable_name(gnb['name'])
                    f.write(f'    gnb_ip = {gnb_name}.IP()\n')
                    f.write(f'    print(f"gNB {gnb_name} IP: {{gnb_ip}}")\n')
                    
                    # Update all UE config files with this gNB IP
                    for ue in categorized_nodes['ues']:
                        ue_name = self.sanitize_variable_name(ue['name'])
                        config_file = f"{ue_name}.yaml"
                        # Replace placeholder with actual gNB IP using double quotes for variable expansion
                        f.write(f'    result = {ue_name}.cmd(f"sed -i \\"s/GNB_CONTAINER_IP_PLACEHOLDER/${{gnb_ip}}/g\\" /config/{config_file}")\n')
                        # Also replace any remaining hardcoded IPs
                        f.write(f'    result = {ue_name}.cmd(f"sed -i \\"s/10.0.0.1/${{gnb_ip}}/g\\" /config/{config_file}")\n')
                        f.write(f'    print(f"Updated {ue_name} config with gNB IP: {{gnb_ip}}")\n')
                        # Verify the change
                        f.write(f'    verify = {ue_name}.cmd("grep gnbSearchList -A1 /config/{config_file}")\n')
                        f.write(f'    print(f"Verification for {ue_name}: {{verify}}")\n')
                        f.write(f'    result = {ue_name}.cmd(f"sed -i \\"s/127.0.0.1/${{gnb_ip}}/g\\" /config/{config_file}")\n')
                        # Verify the change
                        f.write(f'    updated_ip = {ue_name}.cmd("grep gnbSearchList -A1 /config/{config_file} | tail -1 | tr -d \' -\'")\n')
                        f.write(f'    print(f"Updated {ue_name} gNB IP to: {{updated_ip}}")\n')
                    break  # Use first gNB IP for all UEs
                f.write('\n')
            
            for ue in categorized_nodes['ues']:
                ue_name = self.sanitize_variable_name(ue['name'])
                # Use specific UE configuration file for each UE
                config_file = f"{ue_name}.yaml"
                f.write(f'    makeTerm2({ue_name}, cmd="/entrypoint.sh ue /config/{config_file} 2>&1 | tee -a /logging/{ue_name}.log")\n')
            f.write('\n')
            f.write('    CLI.do_sh(net, "sleep 20")\n\n')
            
            # Add UE routing configuration - wait for uesimtun interface to be created
            f.write('    info("*** Waiting for uesimtun interface creation and configuring routes\\n")\n')
            for i, ue in enumerate(categorized_nodes['ues'], 1):
                ue_name = self.sanitize_variable_name(ue['name'])
                props = ue.get('properties', {})
                apn = props.get('UE_APN', 'internet')
                
                # Wait for uesimtun interface to be created
                f.write(f'    # Wait for uesimtun0 interface to be created on {ue_name}\n')
                f.write(f'    ue_found = False\n')
                f.write(f'    for i in range(30):\n')
                f.write(f'        result = {ue_name}.cmd("ip link show uesimtun0 2>/dev/null")\n')
                f.write(f'        if result and "uesimtun0" in result:\n')
                f.write(f'            ue_found = True\n')
                f.write(f'            break\n')
                f.write(f'        CLI.do_sh(net, "sleep 1")\n')
                f.write(f'    \n')
                f.write(f'    if not ue_found:\n')
                f.write(f'        print("Warning: uesimtun0 interface not found on {ue_name}")\n')
                f.write(f'        print("Debug: Available interfaces on {ue_name}:")\n')
                f.write(f'        print({ue_name}.cmd("ip link show"))\n')
                f.write(f'        print("Debug: UE process status:")\n')
                f.write(f'        print({ue_name}.cmd("ps aux | grep nr-ue"))\n')
                f.write(f'    else:\n')
                f.write(f'        # Interface found - show diagnostic info\n')
                f.write(f'        print("✓ uesimtun0 interface found on {ue_name}")\n')
                f.write(f'        interface_info = {ue_name}.cmd("ip addr show uesimtun0")\n')
                f.write(f'        print(f"Interface info: {{interface_info}}")\n')
                f.write(f'        # Configure routes for {ue_name}\n')
                
                # Route based on APN
                if apn == 'internet':
                    f.write(f'        {ue_name}.cmd("ip route add 10.45.0.0/16 dev uesimtun0")\n')
                    f.write(f'        print("✓ Route added: 10.45.0.0/16 via uesimtun0 on {ue_name}")\n')
                elif apn == 'internet2':
                    f.write(f'        {ue_name}.cmd("ip route add 10.46.0.0/16 dev uesimtun0")\n')
                    f.write(f'        print("✓ Route added: 10.46.0.0/16 via uesimtun0 on {ue_name}")\n')
                else:
                    f.write(f'        {ue_name}.cmd("ip route add 10.45.0.0/16 dev uesimtun0")\n')
                    f.write(f'        print("✓ Route added: 10.45.0.0/16 via uesimtun0 on {ue_name}")\n')
                
                f.write(f'        # Test basic connectivity\n')
                f.write(f'        ping_result = {ue_name}.cmd("ping -c 1 -W 2 10.45.0.1 2>/dev/null")\n')
                f.write(f'        if "1 received" in ping_result:\n')
                f.write(f'            print("✓ Basic connectivity test passed on {ue_name}")\n')
                f.write(f'        else:\n')
                f.write(f'            print("⚠ Basic connectivity test failed on {ue_name}")\n')
            f.write('\n')
        
        # Add helper functions for debugging UE interfaces
        if categorized_nodes['ues']:
            f.write('    # Helper functions for checking UE interfaces\n')
            f.write('    def check_ue_interfaces():\n')
            f.write('        """Check all UE interfaces and their status"""\n')
            f.write('        print("\\n=== UE Interface Status ===")\n')
            for ue in categorized_nodes['ues']:
                ue_name = self.sanitize_variable_name(ue['name'])
                f.write(f'        print("\\n{ue_name}:")\n')
                f.write(f'        result = {ue_name}.cmd("ip link show uesimtun0 2>/dev/null")\n')
                f.write(f'        if result and "uesimtun0" in result:\n')
                f.write(f'            print("  ✓ uesimtun0: UP")\n')
                f.write(f'            addr_info = {ue_name}.cmd("ip addr show uesimtun0 | grep inet")\n')
                f.write(f'            if addr_info:\n')
                f.write(f'                print(f"  IP: {{addr_info.strip()}}")\n')
                f.write(f'            route_info = {ue_name}.cmd("ip route show dev uesimtun0")\n')
                f.write(f'            if route_info:\n')
                f.write(f'                print(f"  Routes: {{route_info.strip()}}")\n')
                f.write(f'        else:\n')
                f.write(f'            print("  ✗ uesimtun0: NOT FOUND")\n')
                f.write(f'            print("  Available interfaces:")\n')
                f.write(f'            interfaces = {ue_name}.cmd("ip link show | grep -E \'^[0-9]+:\'")\n')
                f.write(f'            for line in interfaces.split("\\n"):\n')
                f.write(f'                if line.strip():\n')
                f.write(f'                    print(f"    {{line.strip()}}")\n')
            f.write('    \n')
            f.write('    def test_ue_connectivity():\n')
            f.write('        """Test connectivity through UE interfaces"""\n')
            f.write('        print("\\n=== UE Connectivity Test ===")\n')
            for ue in categorized_nodes['ues']:
                ue_name = self.sanitize_variable_name(ue['name'])
                f.write(f'        print("\\nTesting {ue_name}...")\n')
                f.write(f'        # Test ping to UPF\n')
                f.write(f'        ping_result = {ue_name}.cmd("ping -c 2 -W 3 -I uesimtun0 10.45.0.1 2>/dev/null")\n')
                f.write(f'        if "2 received" in ping_result or "1 received" in ping_result:\n')
                f.write(f'            print("  ✓ UPF connectivity: OK")\n')
                f.write(f'        else:\n')
                f.write(f'            print("  ✗ UPF connectivity: FAILED")\n')
                f.write(f'        # Test internet connectivity\n')
                f.write(f'        inet_result = {ue_name}.cmd("ping -c 1 -W 3 -I uesimtun0 8.8.8.8 2>/dev/null")\n')
                f.write(f'        if "1 received" in inet_result:\n')
                f.write(f'            print("  ✓ Internet connectivity: OK")\n')
                f.write(f'        else:\n')
                f.write(f'            print("  ✗ Internet connectivity: FAILED")\n')
            f.write('    \n')
            f.write('    # Add CLI commands for easy debugging\n')
            f.write('    print("\\n=== Available Debug Commands ===")\n')
            f.write('    print("check_ue_interfaces() - Check status of all UE interfaces")\n')
            f.write('    print("test_ue_connectivity() - Test connectivity through UE interfaces")\n')
            f.write('    print("Example: In CLI, type: py check_ue_interfaces()")\n')
            f.write('    print("Example: In CLI, type: py test_ue_connectivity()")\n')
            f.write('    print("Example: Check specific UE: UE_1.cmd(\'ip addr show uesimtun0\')")\n\n')
        
        # Add CLI startup
        f.write('    info("*** Running CLI\\n")\n')
        f.write('    CLI(net)\n\n')
        
        f.write('    info("*** Stopping network\\n")\n')
        f.write('    net.stop()\n\n')

    def extract_5g_components_by_type(self, core5g_components):
        """Extract 5G components organized by type from VGcore configurations."""
        components_by_type = {
            'UPF': [], 'AMF': [], 'SMF': [], 'NRF': [], 'SCP': [],
            'AUSF': [], 'BSF': [], 'NSSF': [], 'PCF': [],
            'UDM': [], 'UDR': []
        }
        
        for vgcore in core5g_components:
            props = vgcore.get('properties', {})
            
            # Look for component configurations in properties
            for comp_type in components_by_type.keys():
                # Look for the new configs format first
                config_key = f"{comp_type}_configs"
                if config_key in props and props[config_key]:
                    config_data = props[config_key]
                    if isinstance(config_data, list):
                        for row_idx, row_data in enumerate(config_data):
                            if isinstance(row_data, dict) and row_data.get('name'):
                                # Extract configuration from new format
                                comp_name = row_data.get('name', f'{comp_type.lower()}{row_idx+1}')
                                config_file = row_data.get('config_filename', f'{comp_type.lower()}.yaml')
                                config_file_path = row_data.get('config_file_path', '')
                                
                                component_info = {
                                    'name': comp_name,
                                    'x': vgcore.get('x', 0),
                                    'y': vgcore.get('y', 0),
                                    'properties': props,
                                    'config_file': config_file,
                                    'config_file_path': config_file_path,
                                    'config_content': row_data.get('config_content', {}),
                                    'imported': row_data.get('imported', False),
                                    'component_type': comp_type,
                                    'row_data': row_data
                                }
                                components_by_type[comp_type].append(component_info)
                
                # Fallback to old table format for backward compatibility
                else:
                    table_key = f'Component5G_{comp_type}table'
                    if table_key in props and props[table_key]:
                        table_data = props[table_key]
                        if isinstance(table_data, list):
                            for row_idx, row_data in enumerate(table_data):
                                if isinstance(row_data, list) and len(row_data) >= 2:
                                    # Extract name and config file from old table format
                                    comp_name = row_data[0] if row_data[0] else f'{comp_type.lower()}{row_idx+1}'
                                    config_file = row_data[1] if len(row_data) > 1 and row_data[1] else f'{comp_type.lower()}.yaml'
                                    
                                    component_info = {
                                        'name': comp_name,
                                        'x': vgcore.get('x', 0),
                                        'y': vgcore.get('y', 0),
                                        'properties': props,
                                        'config_file': config_file,
                                        'config_file_path': '',  # Old format doesn't have file paths
                                        'config_content': {},
                                        'imported': False,
                                        'component_type': comp_type,
                                        'table_row': row_data  # Keep for backward compatibility
                                    }
                                    components_by_type[comp_type].append(component_info)
        
        # Store extracted components for use in startup
        return components_by_type

    def write_propagation_model(self, f, categorized_nodes):
        """Write propagation model configuration for wireless networks."""
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        
        if has_wireless:
            f.write('    info("*** Configuring propagation model\\n")\n')
            f.write('    if WIFI_AVAILABLE:\n')
            f.write('        net.setPropagationModel(model="logDistance", exp=4.5)\n')
            f.write('    else:\n')
            f.write('        print("Propagation model not available in standard Mininet")\n')
            f.write('\n')

    def write_links(self, f, links, categorized_nodes):
        """Write link creation code based on extracted links."""
        if not links:
            return
            
        # Get controller names to filter them out from data links
        controller_names = [self.sanitize_variable_name(ctrl['name']) for ctrl in categorized_nodes.get('controllers', [])]
        
        for link in links:
            source_name = self.sanitize_variable_name(link['source'])
            dest_name = self.sanitize_variable_name(link['destination'])
            
            # Skip links involving controllers (controllers don't have data plane connections)
            if source_name in controller_names or dest_name in controller_names:
                f.write(f'    # Skipping controller link: {source_name} <-> {dest_name} (controllers use control plane)\n')
                continue
            
            # Replace VGcore #1 connections with amf1 connections
            # Handle various possible names for VGcore #1
            if source_name in ["VGcore__1", "VGCore__1", "VGcore_1", "VGCore_1"]:
                source_name = "amf1"
            if dest_name in ["VGcore__1", "VGCore__1", "VGcore_1", "VGCore_1"]:
                dest_name = "amf1"
            
            # Add safety check for node existence
            f.write(f'    # Create link between {source_name} and {dest_name}\n')
            f.write(f'    try:\n')
            f.write(f'        if "{source_name}" in locals() and "{dest_name}" in locals():\n')
            
            # Build link parameters
            link_params = [source_name, dest_name]
            
            # Add link properties if any
            link_props = link.get('properties', {})
            if link_props.get('bandwidth'):
                link_params.append(f"bw={link_props['bandwidth']}")
            if link_props.get('delay'):
                link_params.append(f"delay='{link_props['delay']}'")
            if link_props.get('loss'):
                link_params.append(f"loss={link_props['loss']}")
            
            f.write(f'            net.addLink({", ".join(link_params)})\n')
            f.write(f'        else:\n')
            f.write(f'            print(f"*** Warning: Skipping link - one or both nodes not created: {source_name}, {dest_name}")\n')
            f.write(f'    except Exception as e:\n')
            f.write(f'        print(f"*** Error creating link between {source_name} and {dest_name}: {{e}}")\n')
            f.write(f'    \n')
        f.write('\n')

    def write_plot_graph(self, f, categorized_nodes):
        """Write plot graph configuration for wireless networks."""
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        
        if has_wireless:
            f.write('    if WIFI_AVAILABLE and "-p" not in args:\n')
            f.write('        net.plotGraph(max_x=200, max_y=200)\n')
            f.write('    elif not WIFI_AVAILABLE:\n')
            f.write('        print("Plot graph not available in standard Mininet")\n')
            f.write('\n')

    def write_controller_startup(self, f, categorized_nodes):
        """Write controller startup code."""
        if categorized_nodes['controllers']:
            for controller in categorized_nodes['controllers']:
                ctrl_name = self.sanitize_variable_name(controller['name'])
                f.write(f'    {ctrl_name}.start()\n')
        else:
            f.write('    c0.start()\n')
        f.write('\n')

    def write_ap_startup(self, f, categorized_nodes):
        """Write Access Point startup code."""
        if not categorized_nodes['aps']:
            return
            
        controller_name = 'c0'
        if categorized_nodes['controllers']:
            controller_name = self.sanitize_variable_name(categorized_nodes['controllers'][0]['name'])
            
        for ap in categorized_nodes['aps']:
            ap_name = self.sanitize_variable_name(ap['name'])
            f.write(f'    {ap_name}.start([{controller_name}])\n')
        f.write('\n')

    def write_main_execution(self, f):
        """Write the main execution block."""
        f.write('if __name__ == \'__main__\':\n')
        f.write('    setLogLevel(\'info\')\n')
        f.write('    topology(sys.argv)\n')

    def sanitize_variable_name(self, name):
        """Convert display name to valid Python variable name and network interface name."""
        import re
        # Remove special characters and spaces, keep only alphanumeric and underscores
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '', str(name))
        # Ensure it starts with a letter or underscore
        if clean_name and clean_name[0].isdigit():
            clean_name = 'n' + clean_name
        # Limit length to avoid interface name issues (max 15 chars for interface names)
        # Leave room for -eth0 suffix (5 chars), so max 10 chars for node name
        if len(clean_name) > 10:
            clean_name = clean_name[:10]
        # Ensure it's not empty
        return clean_name or 'node'
    
    def _check_save_status(self):
        """Check if topology should be saved before export and prompt user if needed.
        
        Returns:
            bool: True if export should continue, False if user cancelled
        """
        debug_print("Checking save status before export...")
        
        # Check if there are unsaved changes or no file is saved
        has_unsaved = getattr(self.main_window, 'has_unsaved_changes', False)
        current_file = getattr(self.main_window, 'current_file', None)
        
        debug_print(f"Save status: has_unsaved={has_unsaved}, current_file={current_file}")
        
        # Get topology info for better messaging
        nodes, _ = self.main_window.extractTopology()
        has_components = len(nodes) > 0
        
        debug_print(f"Topology info: {len(nodes)} components found")
        
        if has_unsaved or not current_file:
            # Determine the message based on the situation
            if not current_file:
                title = "Unsaved Topology"
                if has_components:
                    message = (f"The topology has {len(nodes)} component(s) but has not been saved to a file yet.\n\n"
                              "It is recommended to save the topology first to ensure:\n"
                              "• Proper Docker network naming based on filename\n"
                              "• Configuration persistence\n"
                              "• Easier topology management\n\n"
                              "Do you want to save the topology first?")
                else:
                    message = ("The topology has not been saved to a file yet.\n\n"
                              "Although there are no components currently, saving the file first\n"
                              "will ensure proper Docker network naming for any components\n"
                              "you may add to the exported script.\n\n"
                              "Do you want to save the topology first?")
            else:
                title = "Unsaved Changes"
                message = ("The topology has unsaved changes.\n\n"
                          "It is recommended to save the changes first to ensure:\n"
                          "• Latest configuration is used in export\n"
                          "• Proper Docker network naming\n"
                          "• Configuration consistency\n\n"
                          "Do you want to save the changes first?")
            
            # Show dialog with options
            reply = QMessageBox.question(
                self.main_window,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes  # Default to Yes
            )
            
            if reply == QMessageBox.Yes:
                debug_print("User chose to save before export")
                # Try to save the file
                if hasattr(self.main_window, 'file_manager'):
                    # Store current state to check if save was successful
                    old_file = getattr(self.main_window, 'current_file', None)
                    old_unsaved = getattr(self.main_window, 'has_unsaved_changes', False)
                    
                    if not current_file:
                        # No file exists, use Save As
                        self.main_window.file_manager.saveTopologyAs()
                    else:
                        # File exists, just save
                        self.main_window.file_manager.saveTopology()
                    
                    # Check if save was successful by verifying file state changed
                    new_file = getattr(self.main_window, 'current_file', None)
                    new_unsaved = getattr(self.main_window, 'has_unsaved_changes', False)
                    
                    if not current_file and not new_file:
                        # Save As was cancelled (no file selected)
                        return False
                    elif current_file and new_unsaved == old_unsaved and old_unsaved:
                        # Save failed (unsaved state didn't change when it should have)
                        QMessageBox.warning(
                            self.main_window,
                            "Save Failed", 
                            "Failed to save the topology. Please try again."
                        )
                        return False
                        
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "Save Error", 
                        "Unable to save topology. File manager not available."
                    )
                    return False
                    
            elif reply == QMessageBox.Cancel:
                debug_print("User cancelled export")
                # User cancelled the operation
                return False
                
            # If reply == QMessageBox.No, continue with export anyway
            debug_print("User chose to continue export without saving")
        
        debug_print("Save status check passed, proceeding with export")
        return True

    def create_ue_config_files(self, config_dir, categorized_nodes):
        """Create UE configuration files for UERANSIM."""
        config_files_created = 0
        
        # Path to the 5g-configs template directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_config_dir = os.path.join(current_dir, "5g-configs")
        ue_template_path = os.path.join(template_config_dir, "ue.yaml")
        
        for i, ue in enumerate(categorized_nodes.get('ues', []), 1):
            ue_name = self.sanitize_variable_name(ue['name'])
            config_file = f"{ue_name}.yaml"
            dst_path = os.path.join(config_dir, config_file)
            
            # Skip if file already exists
            if os.path.exists(dst_path):
                debug_print(f"DEBUG: UE config file already exists: {config_file}")
                continue
            
            # Get UE configuration from properties
            from manager.configmap import ConfigurationMapper
            props = ue.get('properties', {})
            ue_config = ConfigurationMapper.map_ue_config(props)
            
            # Create UE configuration content
            ue_config_content = self.generate_ue_config_content(ue_config, i)
            
            try:
                with open(dst_path, 'w') as f:
                    f.write(ue_config_content)
                debug_print(f"DEBUG: Created UE config file: {config_file}")
                config_files_created += 1
            except Exception as e:
                error_print(f"ERROR: Failed to create UE config file {dst_path}: {e}")
                
        return config_files_created
    
    def create_gnb_config_files(self, config_dir, categorized_nodes):
        """Create gNB configuration files for UERANSIM."""
        config_files_created = 0
        
        # Path to the 5g-configs template directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_config_dir = os.path.join(current_dir, "5g-configs")
        gnb_template_path = os.path.join(template_config_dir, "gnb.yaml")
        
        for i, gnb in enumerate(categorized_nodes.get('gnbs', []), 1):
            gnb_name = self.sanitize_variable_name(gnb['name'])
            config_file = f"{gnb_name}.yaml"
            dst_path = os.path.join(config_dir, config_file)
            
            # Skip if file already exists
            if os.path.exists(dst_path):
                debug_print(f"DEBUG: gNB config file already exists: {config_file}")
                continue
            
            # Get gNB configuration from properties
            from manager.configmap import ConfigurationMapper
            props = gnb.get('properties', {})
            gnb_config = ConfigurationMapper.map_gnb_config(props)
            
            # Create gNB configuration content
            gnb_config_content = self.generate_gnb_config_content(gnb_config, i)
            
            try:
                with open(dst_path, 'w') as f:
                    f.write(gnb_config_content)
                debug_print(f"DEBUG: Created gNB config file: {config_file}")
                config_files_created += 1
            except Exception as e:
                error_print(f"ERROR: Failed to create gNB config file {dst_path}: {e}")
                
        return config_files_created
    
    def generate_ue_config_content(self, ue_config, ue_index):
        """Generate UE configuration content from template."""
        
        # Get gNB IP - use configured IP or use placeholder for runtime replacement
        gnb_ip = ue_config.get('gnb_ip')
        
        # If no specific gNB IP is configured, use a placeholder that will be replaced at runtime
        if not gnb_ip or gnb_ip in ['127.0.0.1', '10.0.0.1', 'localhost']:
            # Use a unique placeholder that will be replaced with actual gNB IP
            gnb_ip = 'GNB_CONTAINER_IP_PLACEHOLDER'
        
        template_content = f"""# IMSI number of the UE. IMSI = [MCC|MNC|MSISDN] (In total 15 or 16 digits)
supi: 'imsi-{ue_config.get('mcc', '999')}{ue_config.get('mnc', '70')}{ue_config.get('msisdn', f'000000000{ue_index:01d}')}'
# Mobile Country Code value
mcc: '{ue_config.get('mcc', '999')}'
# Mobile Network Code value (2 or 3 digits)
mnc: '{ue_config.get('mnc', '70')}'

# Permanent subscription key
key: '{ue_config.get('key', '465B5CE8B199B49FAA5F0A2EE238A6BC')}'
# Operator code (OP or OPC) of the UE
op: '{ue_config.get('op', 'E8ED289DEBA952E4283B54E88E6183CA')}'
# This value specifies the OP type and it can be either 'OP' or 'OPC'
opType: '{ue_config.get('op_type', 'OPC')}'
# Authentication Management Field (AMF) value
amf: '8000'
# IMEI number of the device. It is used if no SUPI is provided
imei: '{ue_config.get('imei', '356938035643803')}'
# IMEISV number of the device. It is used if no SUPI and IMEI is provided
imeiSv: '{ue_config.get('imeisv', '4370816125816151')}'

# List of gNB IP addresses for Radio Link Simulation
gnbSearchList:
  - {gnb_ip}

# UAC Access Identities Configuration
uacAic:
  mps: false
  mcs: false

# UAC Access Control Class
uacAcc:
  normalClass: 0
  class11: false
  class12: false
  class13: false
  class14: false
  class15: false
  
# Initial PDU sessions to be established
sessions:
  - type: '{ue_config.get('session_type', 'IPv4')}'
    apn: '{ue_config.get('apn', 'internet')}'
    slice:
      sst: {ue_config.get('sst', '1')}
      sd: {ue_config.get('sd', '0xffffff')}
    emergency: false

# Configured NSSAI for this UE by HPLMN
configured-nssai:
  - sst: {ue_config.get('sst', '1')}
    sd: {ue_config.get('sd', '0xffffff')}

# Default Configured NSSAI for this UE
default-nssai:
  - sst: {ue_config.get('sst', '1')}
    sd: {ue_config.get('sd', '0xffffff')}

# Supported encryption algorithms by this UE
integrity:
  IA1: true
  IA2: true
  IA3: true

# Supported integrity algorithms by this UE
ciphering:
  EA1: true
  EA2: true
  EA3: true

# Integrity protection maximum data rate for user plane
integrityMaxRate:
  uplink: 'full'
  downlink: 'full'
"""
        return template_content
    
    def generate_gnb_config_content(self, gnb_config, gnb_index):
        """Generate gNB configuration content from template."""
        
        # Use placeholder for AMF IP that will be replaced at runtime
        amf_ip = gnb_config.get('amf_ip', 'AMF_CONTAINER_IP_PLACEHOLDER')
        
        template_content = f"""# gNB identification
nci: {gnb_config.get('nci', f'0x00000001{gnb_index}')}
idLength: {gnb_config.get('id_length', '32')}
tac: {gnb_config.get('tac', '1')}
mcc: '{gnb_config.get('mcc', '999')}'
mnc: '{gnb_config.get('mnc', '70')}'

# gNB location
gnbSearchList: []

# List of AMF addresses for Registration
amfConfigs:
  - address: {amf_ip}
    port: {gnb_config.get('amf_port', '38412')}

# List of supported S-NSSAIs by this gNB
slices:
  - sst: {gnb_config.get('sst', '1')}
    sd: {gnb_config.get('sd', '0xffffff')}

# Indication of ignoring stream ids of SCTP connections
ignoreStreamIds: true

# gNB NGAP bind address (listen on all interfaces)
ngapIp: 0.0.0.0

# gNB GTP-U bind address (listen on all interfaces)  
gtpIp: 0.0.0.0

# Supported encryption algorithms by this gNB
supportedEncryption:
  - NEA0
  - NEA1
  - NEA2
  - NEA3

# Supported integrity algorithms by this gNB
supportedIntegrity:
  - NIA0
  - NIA1
  - NIA2
  - NIA3

# Paging DRX cycle
pagingDrx: v32

# Served cells information
servedCells:
  - cellId: {gnb_config.get('cell_id', f'0x00000000{gnb_index}')}
    tac: {gnb_config.get('tac', '1')}
    broadcastPlmns:
      - mcc: '{gnb_config.get('mcc', '999')}'
        mnc: '{gnb_config.get('mnc', '70')}'
        taiSliceSupportList:
          - sst: {gnb_config.get('sst', '1')}
            sd: {gnb_config.get('sd', '0xffffff')}
    nrCgi:
      mcc: '{gnb_config.get('mcc', '999')}'
      mnc: '{gnb_config.get('mnc', '70')}'
      nrCellId: {gnb_config.get('cell_id', f'0x00000000{gnb_index}')}

# Supported encryption algorithms by this gNB
supportedEncryption:
  - NEA0
  - NEA1
  - NEA2
  - NEA3

# Supported integrity algorithms by this gNB
supportedIntegrity:
  - NIA0
  - NIA1
  - NIA2
  - NIA3

# Paging DRX cycle
pagingDrx: v32

# RAN UE usage indicator
ranUeUsageIndication: false

# Indicates whether periodic registration update is disabled
disablePeriodicRegistration: false
"""
        return template_content

    def write_container_connectivity(self, f, categorized_nodes):
        """Ensure all Docker containers have proper network connectivity."""
        # Collect all Docker-based containers that need connectivity
        docker_containers = []
        
        # Add 5G core components
        core_components = categorized_nodes.get('core5g_components', {})
        for comp_type, components in core_components.items():
            for component in components:
                comp_name = self.sanitize_variable_name(component.get('name', f'{comp_type.lower()}1'))
                docker_containers.append(comp_name)
        
        # Add gNBs
        for gnb in categorized_nodes['gnbs']:
            gnb_name = self.sanitize_variable_name(gnb['name'])
            docker_containers.append(gnb_name)
        
        # Add UEs
        for ue in categorized_nodes['ues']:
            ue_name = self.sanitize_variable_name(ue['name'])
            docker_containers.append(ue_name)
        
        # Add Docker hosts
        for docker_host in categorized_nodes['docker_hosts']:
            host_name = self.sanitize_variable_name(docker_host['name'])
            docker_containers.append(host_name)
        
        if not docker_containers:
            return
        
        f.write('    # Ensure all Docker containers have network interfaces\n')
        f.write('    containers_without_interfaces = []\n')
        f.write('    \n')
        
        # Check each container for interfaces
        for container_name in docker_containers:
            f.write(f'    if hasattr({container_name}, "intfNames") and not list({container_name}.intfNames()):\n')
            f.write(f'        containers_without_interfaces.append("{container_name}")\n')
        
        f.write('    \n')
        f.write('    # Create a management switch only if containers truly need connectivity\n')
        f.write('    # and no other connectivity mechanism exists\n')
        f.write('    if containers_without_interfaces:\n')
        f.write('        # Check if we already have other switches that could provide connectivity\n')
        f.write('        existing_switches = [name for name in locals() if name.startswith("s") and name[1:].isdigit()]\n')
        f.write('        \n')
        f.write(f'        if {self.auto_create_management_switch} and not existing_switches:\n')
        f.write('            print(f"*** Creating management connectivity for containers: {containers_without_interfaces}")\n')
        f.write('            s999 = net.addSwitch("s999", cls=OVSKernelSwitch, protocols="OpenFlow14")\n')
        f.write('            \n')
        f.write('            for container_name in containers_without_interfaces:\n')
        f.write('                try:\n')
        f.write('                    container = locals()[container_name]\n')
        f.write('                    net.addLink(s999, container)\n')
        f.write('                    print(f"*** Connected {container_name} to management switch")\n')
        f.write('                except Exception as e:\n')
        f.write('                    print(f"*** Warning: Failed to connect {container_name}: {e}")\n')
        f.write('        else:\n')
        f.write('            print(f"*** Skipping management switch - existing switches available: {existing_switches}")\n')
        f.write('    \n')
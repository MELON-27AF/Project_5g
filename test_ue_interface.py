#!/usr/bin/env python3
"""
Test UE Interface Creation
Simple test to verify uesimtun interface is created when UE connects to 5G core
"""

import sys
import os

# Setup Python path for Containernet (works with sudo)
import os
# Try multiple possible Containernet installation paths
containernet_paths = [
    "/home/melon/containernet/containernet",
    "/home/melon/containernet",
    "/opt/containernet",
    "/usr/local/containernet",
    os.path.expanduser("~melon/containernet/containernet"),
    os.path.expanduser("~melon/containernet")
]
containernet_found = False
for path in containernet_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        containernet_found = True
        print(f"✓ Added Containernet path: {path}")
        break
if not containernet_found:
    print("Warning: Containernet path not found, trying import anyway...")

# Try containernet first for Docker support
try:
    from containernet.net import Containernet
    from containernet.node import DockerSta
    from mininet.node import RemoteController, OVSKernelSwitch, Host, Node
    from mininet.log import setLogLevel, info
    from containernet.cli import CLI
    from mininet.link import TCLink, Link, Intf
    from containernet.term import makeTerm as makeTerm2
    CONTAINERNET_AVAILABLE = True
    print("✓ containernet available - using Docker support")
except ImportError as e:
    print(f"Warning: containernet import failed: {e}")
    # Fallback to standard Mininet
    from mininet.net import Mininet
    from mininet.node import RemoteController, OVSKernelSwitch, Host, Node
    from mininet.log import setLogLevel, info
    from mininet.cli import CLI
    from mininet.link import TCLink, Link, Intf
    CONTAINERNET_AVAILABLE = False
    
    # Create fallback classes when containernet is not available
    DockerSta = Host  # Use Host as DockerSta fallback
    
    class Containernet(Mininet):
        """Fallback Containernet class using standard Mininet"""
        def addHost(self, name, **kwargs):
            """Override addHost to filter Docker parameters"""
            # Filter out Docker-specific parameters
            filtered_kwargs = {}
            for key, value in kwargs.items():
                if key not in ["dimage", "dcmd", "network_mode", "cap_add", 
                               "devices", "privileged", "publish_all_ports", 
                               "volumes", "environment"]:
                    filtered_kwargs[key] = value
            return super().addHost(name, **filtered_kwargs)

from subprocess import call
import time

def create_docker_network_if_needed():
    """Create Docker network if it doesn't exist."""
    import subprocess
    network_name = "open5gs-ueransim_default"
    
    try:
        # Check if network exists
        result = subprocess.run(["docker", "network", "ls", "--filter", f"name=^{network_name}$", "--format", "{{.Name}}"],
                              capture_output=True, text=True, check=True)
        
        existing_networks = result.stdout.strip().split("\n")
        if network_name not in existing_networks or not result.stdout.strip():
            print(f"*** Creating Docker network: {network_name}")
            create_result = subprocess.run(["docker", "network", "create", "--driver", "bridge", "--attachable", network_name], 
                                         capture_output=True, text=True, check=True)
            print(f"*** Docker network {network_name} created successfully")
        else:
            print(f"*** Using existing Docker network: {network_name}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Error managing Docker network: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        print("Note: Containers may fail to start if network is not available")
    except FileNotFoundError:
        print("Warning: Docker command not found. Please ensure Docker is installed and running.")
        print("Note: Containers may fail to start if Docker is not available")

def simple_5g_topology():
    """Simple 5G topology with AMF, UPF, gNB, and UE"""
    
    # Create Docker network
    create_docker_network_if_needed()
    
    # Set log level
    setLogLevel('info')
    
    # Create network
    if CONTAINERNET_AVAILABLE:
        net = Containernet(topo=None, build=False, ipBase='10.0.0.0/8')
        print("Using Containernet for Docker containers")
    else:
        net = Mininet(topo=None, build=False, ipBase='10.0.0.0/8')
        print("Using standard Mininet (Docker features disabled)")
    
    info("*** Adding controller\n")
    c0 = net.addController(name='c0', controller=RemoteController)
    
    info("*** Creating 5G Core components\n")
    
    # AMF (Access and Mobility Management Function)
    if CONTAINERNET_AVAILABLE:
        amf1 = net.addHost('amf1',
                           cls=DockerSta, 
                           dimage="adaptive/open5gs:1.0",
                           network_mode="open5gs-ueransim_default",
                           cap_add=["NET_ADMIN"],
                           privileged=True,
                           volumes=[
                               "./config:/etc/open5gs:rw",
                               "./logging:/logging:rw"
                           ],
                           environment={
                               "COMPONENT_NAME": "amf"
                           })
    else:
        amf1 = net.addHost('amf1')
    
    # UPF (User Plane Function)
    if CONTAINERNET_AVAILABLE:
        upf1 = net.addHost('upf1',
                           cls=DockerSta, 
                           dimage="adaptive/open5gs:1.0",
                           network_mode="open5gs-ueransim_default",
                           cap_add=["NET_ADMIN"],
                           privileged=True,
                           volumes=[
                               "./config:/etc/open5gs:rw",
                               "./logging:/logging:rw"
                           ],
                           environment={
                               "COMPONENT_NAME": "upf"
                           })
    else:
        upf1 = net.addHost('upf1')
    
    info("*** Adding gNB\n")
    
    # gNB (Next Generation Node B)
    if CONTAINERNET_AVAILABLE:
        gnb1 = net.addHost('gnb1',
                           cls=DockerSta,
                           dimage="adaptive/ueransim:latest",
                           network_mode="open5gs-ueransim_default",
                           cap_add=["NET_ADMIN"],
                           privileged=True,
                           volumes=[
                               "./config:/config:rw",
                               "./logging:/logging:rw"
                           ])
    else:
        gnb1 = net.addHost('gnb1')
    
    info("*** Adding UE\n")
    
    # UE (User Equipment)
    if CONTAINERNET_AVAILABLE:
        ue1 = net.addHost('ue1',
                          cls=DockerSta,
                          dimage="adaptive/ueransim:latest",
                          network_mode="open5gs-ueransim_default",
                          cap_add=["NET_ADMIN"],
                          privileged=True,
                          volumes=[
                              "./config:/config:rw",
                              "./logging:/logging:rw"
                          ])
    else:
        ue1 = net.addHost('ue1')
    
    info("*** Adding switch\n")
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, protocols="OpenFlow14")
    
    info("*** Creating links\n")
    net.addLink(s1, amf1)
    net.addLink(s1, upf1)
    net.addLink(s1, gnb1)
    net.addLink(s1, ue1)
    
    info("*** Starting network\n")
    net.build()
    c0.start()
    s1.start([c0])
    
    # Create config directories
    call(["mkdir", "-p", "./config"])
    call(["mkdir", "-p", "./logging"])
    
    if CONTAINERNET_AVAILABLE:
        info("*** Starting 5G services\n")
        
        # Start AMF
        makeTerm2(amf1, cmd="open5gs-amfd 2>&1 | tee -a /logging/amf1.log")
        time.sleep(2)
        
        # Start UPF
        makeTerm2(upf1, cmd="/entrypoint.sh open5gs-upfd 2>&1 | tee -a /logging/upf1.log")
        time.sleep(2)
        
        # Get AMF IP and update gNB config
        amf_ip = amf1.IP()
        print(f"AMF IP: {amf_ip}")
        
        # Create basic gNB config
        gnb_config = f"""# gNB configuration
nci: 0x000000001
idLength: 32
tac: 1
mcc: '999'
mnc: '70'

# List of AMF addresses for Registration
amfConfigs:
  - address: {amf_ip}
    port: 38412

# Served PLMNs by this gNB
plmns:
  - mcc: '999'
    mnc: '70'
    tac: 1
    nssai:
      - sst: 1

# NR Cell Configuration
nrCellIdentity: 12345678901
f1apPort: 38472
"""
        
        gnb1.cmd(f'echo "{gnb_config}" > /config/gnb1.yaml')
        
        # Start gNB
        makeTerm2(gnb1, cmd="/entrypoint.sh gnb /config/gnb1.yaml 2>&1 | tee -a /logging/gnb1.log")
        time.sleep(5)
        
        # Get gNB IP and create UE config
        gnb_ip = gnb1.IP()
        print(f"gNB IP: {gnb_ip}")
        
        # Create basic UE config
        ue_config = f"""# UE configuration
supi: 'imsi-999700000000001'
mcc: '999'
mnc: '70'
key: '465B5CE8B199B49FAA5F0A2EE238A6BC'
op: 'E8ED289DEBA952E4283B54E88E6183CA'
opType: 'OPC'
amf: '8000'
imei: '356938035643803'
imeiSv: '4370816125816151'

# List of gNB IP addresses for Radio Link Simulation
gnbSearchList:
  - {gnb_ip}

# Initial PDU sessions to be established
sessions:
  - type: 'IPv4'
    apn: 'internet'
    slice:
      sst: 1
      sd: 0xffffff

# Configured NSSAI for this UE by HPLMN
configured-nssai:
  - sst: 1
    sd: 0xffffff
"""
        
        ue1.cmd(f'echo "{ue_config}" > /config/ue1.yaml')
        
        # Start UE
        makeTerm2(ue1, cmd="/entrypoint.sh ue /config/ue1.yaml 2>&1 | tee -a /logging/ue1.log")
        
        info("*** Waiting for uesimtun interface creation\n")
        
        # Wait for uesimtun interface to be created
        ue_found = False
        for i in range(30):
            result = ue1.cmd("ip link show uesimtun0 2>/dev/null")
            if result and "uesimtun0" in result:
                ue_found = True
                break
            time.sleep(1)
            print(f"Waiting for uesimtun0... ({i+1}/30)")
        
        if not ue_found:
            print("⚠ uesimtun0 interface not found on ue1")
            print("Debug: Available interfaces on ue1:")
            print(ue1.cmd("ip link show"))
            print("Debug: UE process status:")
            print(ue1.cmd("ps aux | grep nr-ue"))
            print("Debug: UE logs:")
            print(ue1.cmd("tail -20 /logging/ue1.log"))
        else:
            print("✓ uesimtun0 interface found on ue1")
            interface_info = ue1.cmd("ip addr show uesimtun0")
            print(f"Interface info: {interface_info}")
            
            # Configure routes for UE
            ue1.cmd("ip route add 10.45.0.0/16 dev uesimtun0")
            print("✓ Route added: 10.45.0.0/16 via uesimtun0 on ue1")
            
            # Test connectivity
            ping_result = ue1.cmd("ping -c 2 -W 3 -I uesimtun0 10.45.0.1 2>/dev/null")
            if "2 received" in ping_result or "1 received" in ping_result:
                print("✓ UPF connectivity: OK")
            else:
                print("✗ UPF connectivity: FAILED")
        
        # Helper function for checking UE interfaces
        def check_ue_interfaces():
            """Check all UE interfaces and their status"""
            print("\n=== UE Interface Status ===")
            print("ue1:")
            result = ue1.cmd("ip link show uesimtun0 2>/dev/null")
            if result and "uesimtun0" in result:
                print("  ✓ uesimtun0: UP")
                addr_info = ue1.cmd("ip addr show uesimtun0 | grep inet")
                if addr_info:
                    print(f"  IP: {addr_info.strip()}")
                route_info = ue1.cmd("ip route show dev uesimtun0")
                if route_info:
                    print(f"  Routes: {route_info.strip()}")
            else:
                print("  ✗ uesimtun0: NOT FOUND")
                print("  Available interfaces:")
                interfaces = ue1.cmd("ip link show | grep -E '^[0-9]+:'")
                for line in interfaces.split("\n"):
                    if line.strip():
                        print(f"    {line.strip()}")
        
        # Add CLI commands for easy debugging
        print("\n=== Available Debug Commands ===")
        print("check_ue_interfaces() - Check status of all UE interfaces")
        print("Example: In CLI, type: py check_ue_interfaces()")
        print("Example: Check specific UE: ue1.cmd('ip addr show uesimtun0')")
        
    info("*** Running CLI\n")
    CLI(net)
    
    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    simple_5g_topology()

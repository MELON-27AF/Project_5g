#!/usr/bin/env python3
"""
Simple test with gNB as Access Point
Demonstrates how UE gets uesimtun interface through wireless connection to gNB AP
"""

import sys
import os
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import RemoteController, OVSKernelSwitch, Host
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from subprocess import call
import time

# Robust Containernet import logic
def import_containernet():
    """Try to import Containernet from various paths"""
    paths_to_try = []
    
    # Get original user info when running under sudo
    original_user = os.environ.get('SUDO_USER', os.environ.get('USER', 'user'))
    user_home = os.path.expanduser(f'~{original_user}') if os.environ.get('SUDO_USER') else os.path.expanduser('~')
    
    # Add various potential Containernet paths
    paths_to_try.extend([
        f'{user_home}/containernet',
        f'{user_home}/Documents/containernet',
        f'{user_home}/projects/containernet',
        '/opt/containernet',
        '/usr/local/containernet',
        '/home/user/containernet'
    ])
    
    print(f"DEBUG: Trying to import Containernet...")
    print(f"DEBUG: Original user: {original_user}, Home: {user_home}")
    
    for path in paths_to_try:
        if os.path.exists(path):
            print(f"DEBUG: Found Containernet path: {path}")
            if path not in sys.path:
                sys.path.insert(0, path)
    
    try:
        from containernet.net import Containernet
        from containernet.node import DockerSta
        print("DEBUG: Successfully imported Containernet!")
        return Containernet, DockerSta, True
    except ImportError as e:
        print(f"DEBUG: Failed to import Containernet: {e}")
        return Mininet, Host, False

# Try to import Containernet
NetClass, NodeClass, using_containernet = import_containernet()

if using_containernet:
    print("DEBUG: Using Containernet with Docker support")
else:
    print("DEBUG: Falling back to standard Mininet (Docker nodes will be regular hosts)")
    # Define DockerSta as alias for Host when Containernet is not available
    DockerSta = Host

def write_gnb_config(gnb_name, amf_ip="10.0.0.10", gnb_ip="10.0.0.20"):
    """Write gNB configuration file"""
    config = f"""mcc: '999'
mnc: '70'
nci: 0x{gnb_name[-1]}
idLength: 22
tac: 1
linkIp: {gnb_ip}
ngapIp: {gnb_ip}
gtpIp: {gnb_ip}

amfConfigs:
  - address: {amf_ip}
    port: 38412

slices:
  - sst: 1
    sd: 0xffffff

ignoreStreamIds: []
"""
    with open(f'/tmp/config/{gnb_name}.yaml', 'w') as f:
        f.write(config)

def write_ue_config(ue_name, gnb_ip="10.0.0.20"):
    """Write UE configuration file"""
    config = f"""supi: 'imsi-999700000000001'
mcc: '999'
mnc: '70'
key: '465B5CE8B199B49FAA5F0A2EE238A6BC'
op: 'E8ED289DEBA952E4283B54E88E6183CA'
opType: 'OPC'
amf: '8000'
imei: '356938035643803'
imeiSv: '4370816125816151'

gnbSearchList:
  - {gnb_ip}

sessions:
  - type: 'IPv4'
    apn: 'internet'
    slice:
      sst: 1
      sd: 0xffffff

configured-nssai:
  - sst: 1
    sd: 0xffffff

default-nssai:
  - sst: 1
    sd: 0xffffff

integrity:
  IA1: true
  IA2: true
  IA3: false

ciphering:
  EA1: true
  EA2: true
  EA3: false
"""
    with open(f'/tmp/config/{ue_name}.yaml', 'w') as f:
        f.write(config)

def start_5g_components(net, nodes):
    """Start 5G components with proper config and startup sequence"""
    info('*** Writing 5G configuration files\n')
    
    # Write config files for UERANSIM components
    for node in nodes:
        node_name = node.name
        if 'gnb' in node_name.lower():
            write_gnb_config(node_name)
            info(f'*** Written config for {node_name}\n')
        elif 'ue' in node_name.lower():
            write_ue_config(node_name)
            info(f'*** Written config for {node_name}\n')
    
    info('*** Starting 5G Core Components\n')
    
    # Start AMF
    for node in nodes:
        if 'amf' in node.name.lower():
            info(f'*** Starting AMF on {node.name}\n')
            node.cmd('open5gs-amfd > /logging/amf.log 2>&1 &')
            break
    
    time.sleep(3)
    
    # Start UPF
    for node in nodes:
        if 'upf' in node.name.lower():
            info(f'*** Starting UPF on {node.name}\n')
            node.cmd('open5gs-upfd > /logging/upf.log 2>&1 &')
            break
    
    time.sleep(5)
    
    # Start gNB
    for node in nodes:
        if 'gnb' in node.name.lower():
            info(f'*** Starting gNB on {node.name}\n')
            node.cmd(f'nr-gnb -c /config/{node.name}.yaml > /logging/gnb.log 2>&1 &')
            break
    
    time.sleep(10)
    
    # Start UE
    for node in nodes:
        if 'ue' in node.name.lower():
            info(f'*** Starting UE on {node.name}\n')
            node.cmd(f'nr-ue -c /config/{node.name}.yaml > /logging/ue.log 2>&1 &')
            break
    
    time.sleep(15)
    info('*** 5G startup sequence completed\n')

def simple_gnb_ap_topology():
    """Simple topology with gNB as AP and UE"""
    
    net = NetClass(build=False, ipBase='10.0.0.0/8')

    info('\n*** Adding controller\n')
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           port=6653)

    info('\n*** Add Switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, protocols="OpenFlow14")

    info('\n*** Add 5G Core Network Components\n')
    
    # Create config and logging directories
    os.makedirs('/tmp/config', exist_ok=True)
    os.makedirs('/tmp/logging', exist_ok=True)
    
    # AMF (Access and Mobility Management Function)
    amf_params = {
        'cls': DockerSta,
        'ip': '10.0.0.10/24'
    }
    
    if using_containernet:
        amf_params.update({
            'dimage': "adaptive/open5gs:1.0",
            'network_mode': "open5gs-ueransim_default",
            'cap_add': ["NET_ADMIN"],
            'publish_all_ports': True,
            'volumes': ["/tmp/config:/config", "/tmp/logging:/logging"],
            'environment': {"COMPONENT_NAME": "amf"}
        })
    
    amf1 = net.addHost('amf1', **amf_params)

    # UPF (User Plane Function)
    upf_params = {
        'cls': DockerSta,
        'ip': '10.0.0.11/24'
    }
    
    if using_containernet:
        upf_params.update({
            'dimage': "adaptive/open5gs:1.0",
            'network_mode': "open5gs-ueransim_default",
            'cap_add': ["NET_ADMIN"],
            'privileged': True,
            'publish_all_ports': True,
            'volumes': ["/tmp/config:/config", "/tmp/logging:/logging"],
            'environment': {"COMPONENT_NAME": "upf"}
        })
    
    upf1 = net.addHost('upf1', **upf_params)

    info('\n*** Add gNB with AP functionality\n')
    # gNB that functions as Access Point
    gnb_params = {
        'cls': DockerSta,
        'ip': '10.0.0.20/24'
    }
    
    if using_containernet:
        gnb_params.update({
            'dimage': "adaptive/ueransim:latest",
            'network_mode': "open5gs-ueransim_default",
            'cap_add': ["NET_ADMIN"],
            'privileged': True,
            'publish_all_ports': True,
            'volumes': ["/sys:/sys", "/lib/modules:/lib/modules", "/tmp/config:/config", "/tmp/logging:/logging"],
            'environment': {
                # 5G Configuration
                "AMF_IP": "10.0.0.10",
                "GNB_HOSTNAME": "mn.gnb1",
                "N2_IFACE": "gnb1-eth0",
                "N3_IFACE": "gnb1-eth0", 
                "RADIO_IFACE": "gnb1-eth0",
                "MCC": "999",
                "MNC": "70",
                "SST": "1",
                "SD": "0xffffff",
                "TAC": "1",
                
                # AP Configuration - Enable AP functionality
                "AP_ENABLED": "true",
                "AP_SSID": "gnb-5g-hotspot",
                "AP_CHANNEL": "6",
                "AP_MODE": "g",
                "AP_PASSWD": "",  # Open network
                "AP_BRIDGE_NAME": "br-gnb1"
            }
        })
    
    gnb1 = net.addHost('gnb1', **gnb_params)

    info('\n*** Add UE (User Equipment)\n')
    # UE that will connect to gNB AP and get uesimtun interface
    ue_params = {
        'cls': DockerSta,
        'ip': '10.0.0.30/24'
    }
    
    if using_containernet:
        ue_params.update({
            'dimage': "adaptive/ueransim:latest",
            'network_mode': "open5gs-ueransim_default",
            'devices': ["/dev/net/tun"],
            'cap_add': ["NET_ADMIN"],
            'privileged': True,
            'volumes': ["/tmp/config:/config", "/tmp/logging:/logging"],
            'environment': {
                # UE Configuration to connect to gnb1
                "GNB_IP": "10.0.0.20",
                "APN": "internet",
                "MSISDN": "0000000001",
                "MCC": "999",
                "MNC": "70",
                "SST": "1", 
                "SD": "0xffffff",
                "TAC": "1",
                "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                "OP_TYPE": "OPC",
                "OP": "E8ED289DEBA952E4283B54E88E6183CA"
            }
        })
    
    ue1 = net.addHost('ue1', **ue_params)

    info('\n*** Add Links\n')
    # Core network links
    net.addLink(s1, s2, cls=TCLink)
    net.addLink(s1, amf1, cls=TCLink)
    net.addLink(s2, upf1, cls=TCLink)
    net.addLink(s1, gnb1, cls=TCLink)
    net.addLink(s2, ue1, cls=TCLink)

    info('\n*** Starting network\n')
    net.build()

    info('\n*** Starting controllers\n')
    c0.start()

    info('\n*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])

    # Set IP addresses manually
    amf1.cmd('ip addr add 10.0.0.10/24 dev amf1-eth0')
    upf1.cmd('ip addr add 10.0.0.11/24 dev upf1-eth0') 
    gnb1.cmd('ip addr add 10.0.0.20/24 dev gnb1-eth0')
    ue1.cmd('ip addr add 10.0.0.30/24 dev ue1-eth0')

    info('\n*** Starting 5G Components\n')
    if using_containernet:
        start_5g_components(net, [amf1, upf1, gnb1, ue1])
    else:
        info('*** Warning: Using standard Mininet - no 5G services will start\n')
        info('*** To get uesimtun interface, run with Containernet support\n')

    info('\n*** Network Setup Complete\n')
    info('*** Checking for uesimtun interface on UE...\n')
    
    # Check if UE got uesimtun interface
    if using_containernet:
        ue_interfaces = ue1.cmd('ip addr show')
        info(f'*** All UE interfaces:\n{ue_interfaces}\n')
        
        uesimtun_check = ue1.cmd('ip addr show | grep uesimtun')
        if 'uesimtun' in uesimtun_check:
            info('✅ SUCCESS: UE got uesimtun interface!\n')
            info('*** uesimtun interface details:\n')
            ue1.cmd('ip addr show uesimtun0')
            info('\n*** Testing 5G connectivity:\n')
            ue1.cmd('ping -c 3 -I uesimtun0 8.8.8.8')
        else:
            info('❌ uesimtun interface not found\n')
            info('*** Checking UERANSIM processes:\n')
            ue1.cmd('ps aux | grep nr-')
            info('\n*** Checking UE logs:\n')
            ue1.cmd('tail -20 /logging/ue.log')
            info('\n*** Checking gNB logs:\n')
            gnb1.cmd('tail -20 /logging/gnb.log')
    else:
        info('❌ Standard Mininet mode - no uesimtun interface expected\n')
        info('*** To get uesimtun, ensure Containernet is properly installed\n')

    info('\n*** Useful Commands:\n')
    if using_containernet:
        info('*** Check UE interfaces: ue1 ip addr\n')
        info('*** Check 5G connection: ue1 ping -I uesimtun0 8.8.8.8\n')
        info('*** View UE logs: ue1 cat /logging/ue.log\n')
        info('*** View gNB logs: gnb1 cat /logging/gnb.log\n')
        info('*** Check UERANSIM processes: ue1 ps aux | grep nr-\n')
        info('*** Check Docker containers: docker ps\n')
    else:
        info('*** Standard Mininet mode - limited 5G functionality\n')
        info('*** Install Containernet for full 5G support\n')

    info('\n*** Running CLI\n')
    CLI(net)

    info('\n*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    simple_gnb_ap_topology()
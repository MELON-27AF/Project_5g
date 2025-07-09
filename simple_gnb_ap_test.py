#!/usr/bin/env python3
"""
Simple test unt    # UPF (User Plane Function)
    upf1 = net.addHost('upf1',
                       cls=DockerSta, 
                       dimage="adaptive/open5gs:1.0",
                       network_mode="open5gs-ueransim_default",
                       cap_add=["NET_ADMIN"],
                       privileged=True,
                       publish_all_ports=True,
                       environment={
                           "COMPONENT_NAME": "upf"
                       })gai Access Point
Mendemonstrasikan bagaimana UE mendapatkan interface uesimtun melalui koneksi wireless ke gNB AP
"""

import sys
import os
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import RemoteController, OVSKernelSwitch, Host
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from containernet.node import DockerSta
from subprocess import call
import time

def simple_gnb_ap_topology():
    """Topologi sederhana dengan gNB sebagai AP dan UE"""
    
    net = Mininet(build=False, ipBase='10.0.0.0/8')

    info('\n*** Adding controller\n')
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           port=6653)

    info('\n*** Add Switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, protocols="OpenFlow14")

    info('\n*** Add 5G Core Network Components\n')
    # AMF (Access and Mobility Management Function)
    amf1 = net.addHost('amf1', 
                       cls=DockerSta,
                       dimage="adaptive/open5gs:1.0",
                       network_mode="open5gs-ueransim_default",
                       cap_add=["NET_ADMIN"],
                       publish_all_ports=True,
                       environment={
                           "COMPONENT_NAME": "amf"
                       })

    # UPF (User Plane Function)
    upf1 = net.addHost('upf1',
                       cls=DockerSta, 
                       dimage="adaptive/open5gs:1.0",
                       network_mode="open5gs-ueransim_default",
                       cap_add=["NET_ADMIN"],
                       privileged=True,
                       publish_all_ports=True,
                       environment={
                           "COMPONENT_NAME": "upf"
                       })

    info('\n*** Add gNB with AP functionality\n')
    # gNB yang berfungsi sebagai Access Point
    gnb1 = net.addHost('gnb1',
                       cls=DockerSta,
                       dimage="adaptive/ueransim:latest",
                       network_mode="open5gs-ueransim_default",
                       cap_add=["NET_ADMIN"],
                       privileged=True,
                       publish_all_ports=True,
                       volumes=["/sys:/sys", "/lib/modules:/lib/modules"],
                       environment={
                           # 5G Configuration
                           "AMF_IP": "10.0.0.10",  # IP AMF
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
                       })

    info('\n*** Add UE (User Equipment)\n')
    # UE yang akan connect ke gNB AP dan mendapat uesimtun interface
    ue1 = net.addHost('ue1',
                      cls=DockerSta,
                      dimage="adaptive/ueransim:latest",
                      network_mode="open5gs-ueransim_default",
                      devices=["/dev/net/tun"],
                      cap_add=["NET_ADMIN"],
                      environment={
                          # UE Configuration untuk connect ke gnb1
                          "GNB_IP": "10.0.0.20",  # IP gNB
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
                      })

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

    info('\n*** Starting 5G Core Components\n')
    # Start AMF
    amf1.cmd('open5gs-amfd > /tmp/amf.log 2>&1 &')
    
    # Start UPF
    upf1.cmd('/entrypoint.sh open5gs-upfd > /tmp/upf.log 2>&1 &')
    
    time.sleep(5)

    info('\n*** Starting gNB with AP functionality\n')
    # Start gNB dengan AP mode enabled
    gnb1.cmd('/entrypoint.sh gnb > /tmp/gnb.log 2>&1 &')
    
    time.sleep(10)

    info('\n*** Starting UE\n')
    # Start UE untuk connect ke gNB dan establish 5G connection
    ue1.cmd('/entrypoint.sh ue > /tmp/ue.log 2>&1 &')
    
    time.sleep(15)

    info('\n*** Network Setup Complete\n')
    info('*** Checking interface uesimtun pada UE...\n')
    
    # Check apakah UE mendapat interface uesimtun
    ue_interfaces = ue1.cmd('ip addr show | grep uesimtun')
    if 'uesimtun' in ue_interfaces:
        info('✅ SUCCESS: UE mendapat interface uesimtun!\n')
        info('Interface uesimtun details:\n')
        ue1.cmd('ip addr show uesimtun0')
        info('\n')
    else:
        info('❌ Interface uesimtun belum terbentuk\n')
        info('Cek log UE untuk troubleshooting:\n')
        ue1.cmd('tail -20 /tmp/ue.log')

    info('\n*** Useful Commands:\n')
    info('Check gNB AP status: gnb1 ovs-vsctl show\n')
    info('Check UE interfaces: ue1 ip addr\n')
    info('Check 5G connection: ue1 ping -I uesimtun0 8.8.8.8\n')
    info('View logs: gnb1 cat /tmp/gnb.log, ue1 cat /tmp/ue.log\n')

    info('\n*** Running CLI\n')
    CLI(net)

    info('\n*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    simple_gnb_ap_topology()
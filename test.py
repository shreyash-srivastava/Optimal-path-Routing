#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)
	#s1.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')
	#s2.cmd('ovs-vsctl set Bridge s2 protocols=OpenFlow13')
	#s3.cmd('ovs-vsctl set Bridge s3 protocols=OpenFlow13')
	#s4.cmd('ovs-vsctl set Bridge s4 protocols=OpenFlow13')
	#s5.cmd('ovs-vsctl set Bridge s5 protocols=OpenFlow13')
	#s1.cmd('ovs-vsctl set-manager ptcp:6632')
	#s2.cmd('ovs-vsctl set-manager ptcp:6632')
	#s3.cmd('ovs-vsctl set-manager ptcp:6632')
	#s4.cmd('ovs-vsctl set-manager ptcp:6632')
	#s5.cmd('ovs-vsctl set-manager ptcp:6632')

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    h3 = net.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
    h4 = net.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(h1, s1, cls=TCLink, bw=1)
    net.addLink(h2, s1, cls=TCLink, bw=1)
    net.addLink(s3, h3, cls=TCLink, bw=1)
    net.addLink(s3, h4, cls=TCLink, bw=1)
    net.addLink(s1, s2, cls=TCLink, bw=1)
    net.addLink(s2, s3, cls=TCLink, bw=1)
    net.addLink(s1, s4, cls=TCLink, bw=1)
    net.addLink(s4, s5, cls=TCLink, bw=1)
    net.addLink(s5, s3, cls=TCLink, bw=1)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])
    net.get('s5').start([c0])

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()


# Optimal-path-Routing
This code is based on Optimal Path routing in Software Defined Networking using Ryu Controller and Mininet network emulator.
This code works in following steps:

1. The topology information is discovered – list of hosts, switches and links.

2. All paths are calculated from one host to other and also the optimal path is listed
based on the topology. Whenever one host pings or transmits packet to the other
host, optimal path is taken and also printed along with all paths.

3. Flow rules are installed from controller to each switch.
The topology used to test the code looks like this-
![image](https://user-images.githubusercontent.com/83832139/130363645-b5edb608-8842-48e9-9642-9923183749d5.png)
First of all ensure that you have installed Ryu SDN Controller and mininet in your machine then procced to run the application.

# REQUIREMENTS-

i) Oracle Virtualbox 6.1

ii) Ubuntu 20.04 installed on a virtualbox VM

iii) Ryu SDN Controller

iv) Mininet network emulator

# INSTALLATION

Install Virtualbox with Ubuntu 20.04 OS-

i) Download Ubuntu 20.04 ISO Image (Desktop Versiion) from http://releases.ubuntu.com/20.04/

ii) Import Ubuntu 20.04 image- 

First, open VirtualBox. Then, click on Machine > New. Now, type in a name for the VM, select Linux from the Type dropdown menu, and Ubuntu (64-bit) from the Version dropdown menu. Then, click on Next >.

iii)In VirtualBox keep settings as-
Base memory – 4096 MB
Storage – 50 GB
Network Adapter 1 : NAT
Network Adapter 2 : Host Only
Network Adapter 3 : Bridged Adapter

iv) Select 'Create a virtual hard disk now' and click on Create.

v) Go to the Storage tab, select the 'Empty IDE device', click on the CD icon, and click on 'Choose Virtual Optical Disk File'

vi) Select the Ubuntu Desktop 20.04 LTS ISO file you downloaded. Click on 'Open' and then 'OK'.

vii) Start VM and install ubuntu.

viii)In VirtualBox Ubuntu install all basic libraries with following commands-

$sudo apt-get update

$sudo apt-get install build-essential

$sudo apt-get install manpages-dev

$sudo apt update

$sudo apt install python3-pip

ix) Install Ryu Controller instructions- https://ryu.readthedocs.io/en/latest/getting_started.html

x) Install mininet instructions - http://mininet.org/download/

# EXECUTION
To run the code-

Open directly containing following code in the terminal, then execute the application using:

$ryu-manager --observe-links short.py

open another terminal, execute the topology file-

$sudo python3 –test.py

Ping between hosts in mininet :

mininet>pingall

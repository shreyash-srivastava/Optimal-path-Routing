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
To run the code-
Open directly containing following code in the terminal, then execute the application using:
$ryu-manager --observe-links short.py
open another terminal, execute the topology file-
$sudo python3 –test.py
Ping between hosts in mininet :
Mininet>pingall

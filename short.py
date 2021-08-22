from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ipv6
from ryu.lib.packet import ether_types
from ryu.lib import mac, ip
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.topology import event

from collections import defaultdict
from operator import itemgetter

import os
import random
import time
import math
import networkx as nx

REFERENCE_BW = 10000000

DEFAULT_BW = 10000000


class CongestionControl(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(CongestionControl, self).__init__(*args, **kwargs)
		self.topology_api_app = self
		self.net = nx.DiGraph()

		# stores the (dpid, in_port) as value to (mac_address) as key:
		# (mac_addr) => (dpid, in_port)
		self.hosts = {}

		self.mac_to_port = {}
		self.datapath_list = {}
		self.arp_table = {}
		self.switches = []
		self.adjacency = defaultdict(dict)
		self.bandwidths = defaultdict(lambda: defaultdict(lambda: DEFAULT_BW))

	def add_ports_to_path(self, path, first_port, last_port):
		p={}
		in_port = first_port
		for s1, s2 in zip(path[:-1], path[1:]):
			out_port = self.adjacency[s1][s2]
			p[s1] = (in_port, out_port)
			in_port = self.adjacency[s2][s1]
		p[path[-1]] = (in_port, last_port)
		return p

	def install_paths(self, src, first_port, dst, last_port, ip_src, ip_dst):
		path, cost = self.get_optimal_path(src, dst)
		self.logger.info("OPtimal path from %s to %s is %s cost %s\n", src, dst, path, cost)

		self.logger.info("Installing path..")
		self.logger.info("src %s, first port %s, dst %s, last port %s", src, first_port, dst, last_port)

		paths_with_port = self.add_ports_to_path(path, first_port, last_port)

		for node in path:
			dp = self.datapath_list[node]
			ofp = dp.ofproto
			ofp_parser = dp.ofproto_parser

			#if node in paths_with_port:
			in_port = paths_with_port[node][0]
			out_port = paths_with_port[node][1]

			match_ip = ofp_parser.OFPMatch(
				eth_type=0x0800, 
				ipv4_src=ip_src, 
				ipv4_dst=ip_dst
			)
			match_arp = ofp_parser.OFPMatch(
				eth_type=0x0806, 
				arp_spa=ip_src, 
				arp_tpa=ip_dst
			)
			actions = [ofp_parser.OFPActionOutput(out_port)]

			self.add_flow(dp, 32768, match_ip, actions)
			self.add_flow(dp, 1, match_arp, actions)
		self.logger.info("Path installed. Output port %s", paths_with_port[src][1])
		return paths_with_port[src][1]


	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		in_port = msg.match['in_port']

		pkt = packet.Packet(msg.data)
		eth = pkt.get_protocol(ethernet.ethernet)
		arp_pkt = pkt.get_protocol(arp.arp)

		# LLDP
		if eth.ethertype == 35020:
			return

		if pkt.get_protocol(ipv6.ipv6):
			match = parser.OFPMatch(eth_type=eth.ethertype)
			actions = []
			self.add_flow(datapath,1 , match, actions)
			return None

		
		# destination mac
		dst = eth.dst
		# source mac
		src = eth.src
		# switch which has send the packet to controller
		dpid = datapath.id

		# self.mac_to_port.setdefault(dpid, {})

		# self.mac_to_port[dpid][src] = in_port

		# if dst in self.mac_to_port[dpid]:
		# 	out_port = self.mac_to_port[dpid][dst]
		# else:
		# 	out_port = ofproto.OFPP_FLOOD

		if src not in self.hosts:
			# if src host record is not present
			self.hosts[src] = (dpid, in_port)

		out_port = ofproto.OFPP_FLOOD
		
		if arp_pkt:
            # print dpid, pkt
			src_ip = arp_pkt.src_ip
			dst_ip = arp_pkt.dst_ip
			if arp_pkt.opcode == arp.ARP_REPLY:
				self.arp_table[src_ip] = src
				h1 = self.hosts[src]
				h2 = self.hosts[dst]
				out_port = self.install_paths(h1[0], h1[1], h2[0], h2[1], src_ip, dst_ip)
				self.install_paths(h2[0], h2[1], h1[0], h1[1], dst_ip, src_ip) # reverse
			elif arp_pkt.opcode == arp.ARP_REQUEST:
				if dst_ip in self.arp_table:
					self.arp_table[src_ip] = src
					dst_mac = self.arp_table[dst_ip]
					h1 = self.hosts[src]
					h2 = self.hosts[dst_mac]
					out_port = self.install_paths(h1[0], h1[1], h2[0], h2[1], src_ip, dst_ip)
					self.install_paths(h2[0], h2[1], h1[0], h1[1], dst_ip, src_ip) # reverse
		
		

		actions = [parser.OFPActionOutput(out_port)]

		# # install a flow to avoid packet_in next time
		# if out_port != ofproto.OFPP_FLOOD:
		# 	match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
		# 	# verify if we have a valid buffer_id, if yes avoid to send both
			# flow_mod & packet_out
			# if msg.buffer_id != ofproto.OFP_NO_BUFFER:
			# 	self.add_flow(datapath, 1, match, actions, msg.buffer_id)
			# 	return
			# else:
			# 	self.add_flow(datapath, 1, match, actions)
		data = None
		if msg.buffer_id == ofproto.OFP_NO_BUFFER:
			data = msg.data

		out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,in_port=in_port, actions=actions, data=data)
		datapath.send_msg(out)



	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		match = parser.OFPMatch()
		actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
		                                  ofproto.OFPCML_NO_BUFFER)]
		self.add_flow(datapath, 0, match, actions)

	def add_flow(self, datapath, priority, match, actions, buffer_id=None):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
		                                     actions)]
		if buffer_id:
		    mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
		                            priority=priority, match=match,
		                            instructions=inst)
		else:
		    mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
		                            match=match, instructions=inst)
		datapath.send_msg(mod)

	@set_ev_cls(event.EventSwitchEnter)
	def switch_enter_handler(self, ev):
		switch = ev.switch.dp
		ofp_parser = switch.ofproto_parser

		self.logger.info("New switch added. (dpid %s). Topology changed", switch.id)

		if switch.id not in self.switches:
			self.switches.append(switch.id)
			self.datapath_list[switch.id] = switch

			# request port/link description for obtaining bandwidth
			req = ofp_parser.OFPPortDescStatsRequest(switch)
			switch.send_msg(req)
		
	def get_paths(self, src, dst):
		'''
		Get all paths from src to dst using DFS algorithm    
		'''
		if src == dst:
		    # host target is on the same switch
		    return [[src]]
		paths = []
		stack = [(src, [src])]
		while stack:	
			(node, path) = stack.pop()
			for next in set(self.adjacency[node].keys()) - set(path):
				if next is dst:
					paths.append(path + [next])
				else:
					stack.append((next, path + [next]))
		self.logger.info("Available paths from " + str(src) + " to " + str(dst)+ " : " + str(paths))
		return paths

	def get_path_cost(self, path):
		'''
		Get the cost of each path
		'''
		cost = 0
		for i in range(len(path) - 1):
			cost += self.get_link_cost(path[i], path[i+1])
		return cost
		
	def get_link_cost(self, s1, s2):
		'''
		Get the link cost between two switches 
		'''
		e1 = self.adjacency[s1][s2]
		e2 = self.adjacency[s2][s1]
		bl = min(self.bandwidths[s1][e1], self.bandwidths[s2][e2])
		ew = REFERENCE_BW/bl
		return ew
	
	@set_ev_cls(event.EventLinkAdd, MAIN_DISPATCHER)
	def link_add_handler(self, ev):
		s1 = ev.link.src
		s2 = ev.link.dst
		self.adjacency[s1.dpid][s2.dpid] = s1.port_no
		self.adjacency[s2.dpid][s1.dpid] = s2.port_no


	def get_optimal_path(self, src, dst):
		paths = self.get_paths(src, dst)
		cost = math.inf
		optimal_path = []
		for path in paths:
			cost_path = self.get_path_cost(path)
			if cost_path < cost:
				optimal_path = path
				cost = cost_path
		return (optimal_path, cost)
	
	@set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
	def port_desc_stats_reply_handler(self, ev):
		switch = ev.msg.datapath
		for p in ev.msg.body:
			self.bandwidths[switch.id][p.port_no] = p.curr_speed
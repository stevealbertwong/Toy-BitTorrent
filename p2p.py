"""
P2P protocol(each torrent)
"""

class PeersP2PProtocol(ClientFactory): ## track exchanging blocks of file progress from all peers
	def __init__(self, torrent, rctr, peer):
		self.reactor = rctr
		self.torrent = torrent
		self.protocols = [] ## 1 protocol == connection with 1 peer, track exchanging blocks of file progress
		self.peer = peer

	def startedConnecting(self, connector): ## starting connection to peer
		## TODO

	def buildProtocol(self, addr):
		protocol = PeerProtocol(self, self.reactor, self.peer) ## each peer
		self.protocols.append(protocol)
		return protocol

	def clientConnectionLost(self, connector, reason):
		self.torrent.remove_active_peer(self.peer)
		# TODO: remove the protocol from self.protocols

"""
P2P protocol(each peer) -> handler definition
	handshake 
	exchanging blocks of files with this peer

"""
class PeerProtocol(Protocol): ## 1 connection of 1 peer exchange file progress
	def __init__(self, factory, rctr, peer):
		self.reactor = rctr ## callback handler
		self.factory = factory ## all torrents
		self.peer = peer
		self.handshake_exchanged = False
		self.stream_processor = StreamProcessor(self.factory.torrent)
		self.outgoing_messages = []

	#####################################################
	# APIs
	#
	#####################################################

	def handshake(self): 
		self.transport.write(self.factory.torrent.marshal_handshake_packet()) ## handshake this peer

	def p2p_receive_messages(self, data):
		self.parse_handle_stream(data)
		self.p2p_send_messages()
		# adds deferred callback for killing the connection due to inactivity
		self.reactor.callLater(PEER_INACTIVITY_LIMIT, self.disconnect_with_inactivity) 


	#####################################################
	# handlers 
	#
	#####################################################

	def parse_handle_stream(self, data): 
		self.stream_processor.parse_stream(stream_data=data) ## parse()
		self.peer.received_messages(self.stream_processor.get_complete_messages()) ## call handler()
		self.stream_processor.purge_complete_messages()


	def p2p_send_messages(self): ## peer's msgs	+ your outgoing msgs
		if self.handshake_exchanged: ## cut ties if info_hash does not match
			if self.peer.info_hash != self.factory.torrent.generate_hex_info_hash():
				self.transport.loseConnection()

		self.factory.torrent.process_next_round(self.peer) ## check torrent how to proceed		
		self.outgoing_messages += self.peer.marshall_msgs_to_outgoing_buffer() ## TODO: now only Request Msg
		
		for outgoing_message in self.outgoing_messages:
			self.transport.write(outgoing_message.message()) ## HTTP send
			self.peer.update_last_contact() ## heartbeat/keepalive
		self.outgoing_messages = []

	def disconnect_with_inactivity(self): ## deferred callback -> remove a peer if inactive for some time 
		current_time = time.time()
		if current_time - self.peer.time_of_last_message > PEER_INACTIVITY_LIMIT:
			if not self.peer.handshake_exchanged:
				self.transport.loseConnection()
			else:
				self.transport.loseConnection()
		else:
			pass

"""
major overall data structure	
	Tracker/DNS status 
	peers status 
	blocks/pieces of files status 

APIs:
	read + populate a .torrent file config
	Tracker Protocol
	handshake peers
	write peers piece messages to temp file in disk + assign next piece

init when:
	browser added torrent
	GUI application 

"""
class Torrent:
	def __init__(self, peer_id, port, torrent_file_path):
		self.metadata = { ## .torrent file's metadata
			"info": None,"announce": None,"announce-list": None,"creation_date": None,
			"comment": None,"created_by": None,"encoding": None,"piece_length": None,
			"pieces": None
		}
		self.tracker_request = { ## placeholder for tracker request
			"info_hash": None,"peer_id": None,"port": None,"uploaded": 0,
			"downloaded": 0,"left": None,"compact": 0,"no_peer_id": 0,
			"event": "started","ip": None,"numwant": 200,"key": None,
			"trackerid": None
		}		
		self.tracker_response = { ## placeholder for tracker's response
			"failure reason": None,"warning message": None,"interval": None,"min interval": None,
			"tracker id": None,"complete": None,"incomplete": None,"peers": None,
		}

		## about yourself 
		self.peer_id = peer_id ## peer id of yourself
		self.port = port ## your port forwarding port 
		self.torrent_file_path = torrent_file_path
		self.torrent_name = None
		self._announce = None ## whether you are tracker
		self.download_root = os.path.join(os.path.expanduser("~"), "Downloads/")
		self.temporary_download_location = None
		make_dir(os.path.join(self.download_root)) ## temp dir for piece downloading		
		self.initialize_previously_downloaded_progress() ## start from progress from earlier session

		## Tracker/DNS -> peer list
		self.tracker_request["peer_id"] = peer_id ## init Tracker Request packet common fields
		self.tracker_request["port"] = port ## your port
		self.tracker_request["info_hash"] = self.generate_info_hash()
		self.tracker_request["left"] = self.metadata["info"]["length"]
		self.activity_status = ACTIVITY_INITIALIZE_NEW
		self.tracker_request_sent = False
		self.is_complete = False
		self.last_request = None ## periodically update Tracker/get updated peers(seeder + leecher)		
		self.reannounce_limit = None
		self.metadata_initialized = False
		self.event_set = False
		self.last_response_object = None
		
		## blocks of file progress + peers 
		self.bitfield = []	## 1 bit = 1 piece completed or not -> inform other peers what you have/need
		self.pieces_hashes = [] ## 20-byte, SHA1-hash of piece -> verify downloaded piece, included in .torrent
		self.peers = [] ## updated list of Peer objects -> get from Tracker's response
		self.active_peers = [] ## all peers that replied handshake()
		self.active_peer_indices = []
		self.assigned_pieces = []
		self.connected_peers = 0
		
		self.initialize_metadata_from_file() ## init from .torrent file

	#####################################################
	# init
	#
	#####################################################

	def initialize_metadata_from_file(self): ## populates self.metadata from .torrent
		with open(self.torrent_file_path, "r") as metadata_file:
			metadata = metadata_file.read()
			self.metadata_initialized = True
			decoded_data = bencode.bdecode(metadata)
			self._announce = decoded_data["announce"]
			self.metadata["info"] = decoded_data["info"]
			self.metadata["piece_length"] = decoded_data["info"]["piece length"]
			self.metadata["pieces"] = decoded_data["info"]["pieces"]
			self.torrent_name = self.metadata["info"]["name"]			
			self.download_root = os.path.join(self.download_root, self.torrent_name)
			
			self.initialize_pieces() ## the most important init
			
			meta_keys = decoded_data.keys() ## optional fields if they exist
			if "announce-list" in meta_keys:
				self.metadata["announce_list"] = decoded_data["announce-list"]
			if "creation date" in meta_keys:
				self.metadata["creation_date"] = decoded_data["creation date"]
			if "comment" in meta_keys:
				self.metadata["comment"] = decoded_data["comment"]
			if "created by" in meta_keys:
				self.metadata["created_by"] = decoded_data["created by"]
			if "encoding" in meta_keys:
				self.metadata["encoding"] = decoded_data["encoding"]			
	
	def initialize_pieces(self): ## init self.pieces_hashes(from .torrent) + self.bitfield(all 0, not yet downloaded)
		self.pieces_hashes = [self.metadata["pieces"][x:x+20] for x in range(0, len(self.metadata["pieces"]), 20)]
		for x in range(0, (len(self.metadata["info"]["pieces"]) / 20)):
			self.bitfield.append(0)

	def initialize_previously_downloaded_progress(self): ## fill self.bitfield from previous DL
		piece_files = [f for f in os.listdir(self.temporary_download_location) if
					   os.path.isfile(os.path.join(self.temporary_download_location, f))]
		for file_name in piece_files:
			self.bitfield[int(file_name.split(".")[0])] = 1
	
	#####################################################
	# APIs
	#
	#####################################################
	def start_torrent(self): 
		self.send_tracker_request()
		self.handshake_peers()
		reactor.run(installSignalHandlers=False)

	def process_next_round(self, peer): ## called after peer has finished sending 1 piece
		## verify + possess the received piece
		if peer.current_piece is not None and peer.current_piece.is_complete: ## peer done dl current piece
			piece_to_save = peer.current_piece
			if piece_to_save.data_matches_hash(): ## check for corruption
				self.exchange_completed_piece_for_new_piece(peer) ## assign a new piece
			else: ## corrupted -> send response
				peer.update_next_piece(piece_to_save.reset())
			self.update_completion_status()

		elif peer.current_piece is None and peer.received_bitfield(): ## not assigned a piece yet			
			peer.set_piece(self.get_next_piece_for_download(peer))
		elif not peer.received_bitfield(): ## no bitfield yet -> need bitfield before assigned a piece
			pass						
		else: ## no update from torrent 
			pass

	def marshal_handshake_packet(self): ## API, called after you got Tracker's response
		## creates Handshake Msg object -> newly connected peer
		info_hash = self.generate_hex_info_hash()
		peer_id = self.peer_id
		handshake_message = HandshakeMessage(info_hash=info_hash, peer_id=peer_id).message()
		return handshake_message

	def compile_file_from_pieces(self, preserve_tmp=False): ## API, called when activity_status -> ACTIVITY_COMPLETED
		## write pieces into a temp file in disk
		output_file_path = os.path.join(one_directory_back(self.temporary_download_location), self.torrent_name)		
		with open(output_file_path, 'w') as output_file:
			for piece in sorted(os.listdir(self.temporary_download_location)): ## each piece is a file
				piece_path = os.path.join(self.temporary_download_location, piece)
				if ".iso" not in piece:					
					with open(piece_path, "r") as piece_file:
						output_file.write(piece_file.read()) ## append each piece of file together

	def stop_torrent(self): 
		self.activity_status = ACTIVITY_STOPPED
		self.connected_peers = 0
		self.active_peers = []
		self.active_peer_indices = []
		self.assigned_pieces = []

	def resume_torrent(self): 
		self.activity_status = ACTIVITY_DOWNLOADING
		self.handshake_peers()


	#####################################################
	# major methods that supports these APIs
	#
	#####################################################

	def send_tracker_request(self):	
		self.tracker_request_sent = True
		tracker_request_packet = self.marshall_tracker_request() ## tracker_request_packet -> string
		try:
			response = requests.get(tracker_request_packet, timeout=RESPONSE_TIMEOUT)
			self.process_tracker_response(response)
		except requests.exceptions.Timeout: ## re-sends if no response in RESPONSE_TIMEOUT secs			
			self.send_tracker_request()

	def handshake_peers(self): ## tcp handshake all peers 1 by 1		
		loops = 0
		while len(self.active_peers) < MAX_PEERS:
			if loops < len(self.peers):
				loops += 1
				current_peer_index = self.connected_peers % len(self.peers)
				current_peer = self.peers[current_peer_index]
				if current_peer not in self.active_peers:
					reactor.connectTCP(current_peer.ip, current_peer.port, PeersP2PProtocol(self, reactor, current_peer))
					self.active_peers.append(current_peer)
					self.connected_peers += 1
			else:
				break

	def marshall_tracker_request(self): ## your node_id + port filled when init Torrent
		request_text = "{}?info_hash={}".format(self._announce, self.tracker_request["info_hash"]) ## filename
		for request_field in self.tracker_request.keys():
			field_data = self.tracker_request[request_field]
			if request_field is not "info_hash" and field_data is not None:
				## standard CGI methods ('?' after announce URL, followed by 'param=value', separated by '&')
				request_text += "&{}={}".format(request_field, field_data)
		return request_text ## Tracker Request packet in string 

	def process_tracker_response(self, tracker_response): ## parse Tracker Request + update torrent object 
		self.last_response_object = tracker_response
		response_text = tracker_response.text
		decoded_response = bencode.bdecode(response_text)
		for response_field in decoded_response.keys():
			self.tracker_response[response_field] = decoded_response[response_field]
		self.populate_peers()

	def populate_peers(self): ## init Peer objects from tracker response's peers[{node_id, ip, port}]
		chunked_peers = self.chunk_bytestring(self.tracker_response["peers"])
		for peer_id_ip_port in chunked_peers:
			new_peer = Peer(self, peer_id_ip_port)
			self.peers.append(new_peer)

	def exchange_completed_piece_for_new_piece(self, peer): ## after piece downloaded, flush() + assigned a new
		# self.assigned_pieces.remove(peer.current_piece.get_index())
		self.bitfield[peer.current_piece.get_index()] = 1 ## update bitfields to be completed		
		peer.current_piece.write_to_temporary_storage() ## temp_file.write(datum) -> flush() to disk
		next_piece = self.get_next_piece_for_download(peer)
		peer.update_next_piece(next_piece)

	def get_next_piece_for_download(self, peer):
		for index, bit in enumerate(self.bitfield): ## sequntially download pieces from each peer -> if not dl yet from another peer
			#print ("current_index: {}\nassigned: {}\nbitfield at index: {}".format(index,", ".join(str(c) for c in self.assigned_pieces), self.bitfield[index]))
			if index not in self.assigned_pieces and self.bitfield[index] == 0: ## found next piece				
				next_hash = self.pieces_hashes[index]
				next_piece = Piece(self.metadata["piece_length"], index, next_hash, self.download_root)
				self.assigned_pieces.append(index) ## list of assigned 
				#print ("Assigned: {}".format(",".join(str(x) for x in self.assigned_pieces)))
				return next_piece

	#####################################################
	# helper methods
	#
	#####################################################

	def can_request(self): ## if its time torrent could contact Tracker
		""" 
		Tracker response
		---------------------------------------------------------------------------
		interval: Interval in seconds that the client should wait between sending
			regular requests to the tracker
		min interval: (optional) Minimum announce interval. If present clients must
			not reannounce more frequently than this.
		---------------------------------------------------------------------------
		"""	
		if self.last_request is not None:
			time_since_request = time.time() - self.last_request
			if self.tracker_response["interval"] is None:
				return True
			elif time_since_request > self.tracker_response["interval"]:
				return True

	def generate_info_hash(self): ## URL-encoded, hex hash of bencoded .torrent's info
		bencoded_info_dict = bencode.bencode(self.metadata["info"])
		sha1_hash = hashlib.sha1(bencoded_info_dict).digest()		 
		url_encoded_hash = urllib.quote(sha1_hash, safe="-_.!~*'()")
		return url_encoded_hash

	def remove_active_peer(self, peer): ## removes a peer from the torrent's peer list
		self.active_peers.remove(peer) ## remove that 1 peer
		if peer.current_piece is not None:
			try:
				self.assigned_pieces.remove(peer.current_piece.get_index())
			except Exception as e:
				pass
		self.handshake_peers()

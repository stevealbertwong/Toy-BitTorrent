"""
1 block of file downloaded from a peer
	-> download status

e.g. 
	Piece(524288, 1670, "test_hash", os.path.join(os.path.expanduser("~"), "Downloads/"))
	piece size -> 64KB - 16MB

"""
class Piece: 
	def __init__(self, piece_length, index, hash, download_location):
		self.piece_length = piece_length ## determined by .torent file
		self.index = index
		self.hash = hash
		self.temp_location = os.path.join(download_location, "tmp", "{}.piece".format(str(self.index).zfill(8)))
		self.data = [] ## sub-pieces / datum
		self.progress = 0.0 ## % of pieces, total count -> indicates by 1 byte of pieces
		self.is_complete = False ## done downloading this entire piece
		self.completed_request_indices = [] ## completed indices of datum of this piece -> DL status
		self.non_completed_request_indices = [] ## non-completed indices of datum of this piece -> DL status

		for x in range(0, self.piece_length):
			self.data.append(0)

	#####################################################
	# major APIs
	#
	#####################################################

	def append_data(self, piece_message): ## Piece Msg -> Piece (each Piece Msg doesn't contain entire piece)
		for x in range(0, len(piece_message.block)):
			self.data[piece_message.get_begin() + x] = piece_message.block[x] ## write to Piece, start at block index

		self.completed_request_indices.append(piece_message.get_begin()) ## update Piece DL status
		self.non_completed_request_indices.remove(int(piece_message.get_begin()))
		self.update_progress()

	def get_next_datum(self): ## Request Msg -> index of next sub-piece, assuming sequential download of datum 
		if len(self.non_completed_request_indices + self.completed_request_indices) > 0:
			return max(self.non_completed_request_indices + self.completed_request_indices) + REQUEST_SIZE
		else:
			return 0

	def write_to_temporary_storage(self): ## called when finish downloading 1 entire piece
		if self.is_complete:
			with open(self.temp_location, "w") as temp_file:
				for datum in self.data:
					temp_file.write(datum)
		
	#####################################################
	# helpers API
	#
	#####################################################

	def update_progress(self):
		self.progress = ((len(self.data) - self.data.count(0)) / float(len(self.data))) * 100

	def add_non_completed_request_index(self, request_message):
		self.non_completed_request_indices.append(int(request_message.get_begin()))

	def non_completed_request_exists(self, request_message):
		return request_message.get_begin() in self.non_completed_request_indices

	def data_matches_hash(self):
		current_hash = hashlib.sha1("".join(byte for byte in self.data)).digest()
		return current_hash == self.hash

	def get_index(self):
		return self.index

	def progress_string(self):
		bars_to_render = int((self.progress / 100.0) * DOWNLOAD_BAR_LEN)
		return u"{}% {}".format(str(self.progress).rjust(6), bars_to_render * u'\u2588')

	def reset(self):
		self.data = []
		self.progress = 0.0
		self.is_complete = False
		self.completed_request_indices = []
		self.non_completed_request_indices = []

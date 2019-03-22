class Main: 
	"""
	1. init Torrent object from .bt file 
	2. start/stop/resume torrent
	"""
	def __init__(self): 
		self.active_torrents = [] ## list of torrents downloading
		self._peer_id = self.generate_peer_id() ## your node id
		self._coast_port = self.get_open_port()
		self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
		self.run_thread = None ## multithread each torrent -> non blocking
		self.displayed_torrent = 0 ## GUI front ground displaying torrent 
		
	def add_torrent_from_browser(self): ## with a magnet link, or from a file		
		torrent_file_path = tkFileDialog.askopenfilename(parent=self, initialdir=self.download_dir, 
			title="Select torrent file to download")
		new_torrent = Torrent(self._peer_id, self._coast_port, torrent_file_path)
		self.active_torrents.append(new_torrent)
	
	def control_torrents(self): ## threaded, non blocked I/O -> program flow + update torrent status 
		for torrent in self.active_torrents:
			if torrent.activity_status == ACTIVITY_COMPLETED:
				torrent.compile_file_from_pieces(preserve_tmp=DEBUG) ## completed DL
				torrent.stop_torrent()

			if torrent.activity_status == ACTIVITY_INITIALIZE_NEW or ACTIVITY_INITIALIZE_CONTINUE:				
				torrent.start_torrent() ## init torrent

			if torrent.activity_status == ACTIVITY_DOWNLOADING:				
				torrent.update_completion_status() ## downloading torrent
				
			if torrent.activity_status == ACTIVITY_STOPPED:		
				torrent.stop_torrent()			

	def run_cmd(self):
		new_torrent = Torrent(self._peer_id, self._coast_port, str(torrent_file_path))		
		self.active_torrents.append(new_torrent)
		self.run_thread = threading.Thread(target=self.control_torrents)
		self.run_thread.start()

	def main(argv):
		run_core = Core()
		run_core.run_cmd()	

"""
Constants used across the project
"""

PROTOCOL_STRING = "BitTorrent protocol"
ERROR_BYTESTRING_CHUNKSIZE = "Input not divisible by chunk size"
MAX_PEERS = 40
REQUEST_SIZE = 16384	 				# 16kb (deluge default)
MAX_OUTSTANDING_REQUESTS = 10			# set to 10-15 in production
PEER_INACTIVITY_LIMIT = 30				# set to 60-120 (seconds) in production
ARGUMENT_PARSING_ERROR_MESSAGE = "core.py -m <mode> [cmd | gui]"

# Client information
CLIENT_ID_STRING = "CO"
CURRENT_VERSION = "0001"

# Networking
RUNNING_PORT = 6881
LISTENING_PORT_MIN = 6881
LISTENING_PORT_MAX = 6889
RESPONSE_TIMEOUT = 5
DOWNLOAD_SPEED_CALCULATION_WINDOW = 5 	# seconds

# Formatting
DOWNLOAD_BAR_LEN = 20

# Activity
ACTIVITY_INITIALIZE_NEW = 			0
ACTIVITY_INITIALIZE_CONTINUE = 		1
ACTIVITY_DOWNLOADING = 				2
ACTIVITY_STOPPED = 					3
ACTIVITY_COMPLETED = 				4

# Debugging
DEBUG = True

NEW_WINDOW_X = 500
NEW_WINDOW_Y = 0

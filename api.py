import time
# Default values
BUFFER_SIZE = 65536                     # The buffer size is the maximum amount of data that can be received at once
DEFAULT_SERVER_HOST = "127.0.0.1"       # The default host for the server
DEFAULT_SERVER_PORT = 9997              # The default port for the server


# ========================================================================
# =============================== QUIC API ===============================
# ========================================================================

# region QUIC 

'''
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|S|Typ|  Next   |              Magic "uic"/"UIC"                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                         Connection ID                         +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Packet Number                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       [Header Extensions]                   ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Payload                           ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''

class QuicPacket:
    sequence = 0 ;   # static variable to keep track of the overall sequence number

    def __init__(self, pos, payload, id):
        QuicPacket.sequence += 1
        self.seq = QuicPacket.sequence
        self.pos = pos
        self.payload = payload
        self.connection_id = id
    
    def __str__(self):
        return f"Seq: {self.seq}, Pos: {self.pos}, Connection ID: {self.connection_id}, Payload size: {len(self.payload)}"
    
    
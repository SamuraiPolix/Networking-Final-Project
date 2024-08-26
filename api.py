import time     
import socket       
import threading    # For handling multiple streams
import struct       # For packing and unpacking data


# Default values
BUFFER_SIZE = 65536                     # The buffer size is the maximum amount of data that can be received at once
DEFAULT_SERVER_HOST = "127.0.0.1"       # The default host for the server
DEFAULT_SERVER_PORT = 9997              # The default port for the server


# ========================================================================
# =============================== QUIC API ===============================
# ========================================================================

# region QUIC Packet

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

# Connection IDs explaied

class QuicPacket:
    sequence = 0 ;   # static variable to keep track of the overall sequence number

    def __init__(self, packet_number, payload, id):
        # Long Header as suggested in RFC 8999 Section 5.1
        self.header_form = 1                     # Header Form (0 - Short, 1 - Long)
        self.version_specific_bits = 0           # not used - Version-Specific Bits (7 bits)
        self.version = 0                         # not used - Version (32 bits)
        self.destination_connection_id_length = 0  # not used - Destination Connection ID Length (8 bits)
        self.destination_connection_id = 0      # Destination Connection ID (0..2040 bits, we set it to 1 bit to allow only 2 connection IDs)
        self.source_connection_id_length = 0      # not used - Source Connection ID Length (8 bits)
        self.source_connection_id = 0           # Source Connection ID (0..2040 bits, we set it to 1 bit to allow only 2 connection IDs)
        # self.version_specific_data = 0          # not used - Version-Specific Data (..)
        self.payload_length = len(payload)       # used instead of above comment, Payload Length (0..2^16-1, 16 bits)
        self.payload = payload                   # Payload (0..2^16-1)
    
    def __str__(self):
        return f"Seq: {self.seq}, Pos: {self.pos}, Connection ID: {self.connection_id}, Payload size: {len(self.payload)}"
    
    '''
    Packing and unpacking:
    !: represents network byte order (big-endian)
    B: unsigned char (1 byte - 8 bits)
    H: unsigned short (usually 2 bytes - 16 bits)
    I: unsigned int (usually 4 bytes - 32 bits)

    We do this because that our way to control the sizing of the fields in the packet in python
    '''
    def pack_long(self):
        # Packs all the data into a byte stream
        return struct.pack('!BBIBBBBH', self.header_form, self.version_specific_bits, self.version, self.destination_connection_id_length, self.destination_connection_id, self.source_connection_id_length, self.source_connection_id, self.version_specific_data, len(self.payload)) + self.payload
    
    def unpack_long(self, data):
        # Unpacks the byte stream into the object
        self.header_form, self.version_specific_bits, self.version, self.destination_connection_id_length, self.destination_connection_id, self.source_connection_id_length, self.source_connection_id, self.version_specific_data, self.payload_length = struct.unpack('!BBIBBBBH', data[:16])
        self.payload = data[16:]
        
    def pack_short(self):
        # Packs only header_form, version_specific_bits, destination_connection_id, version_specific_data and payload
        return struct.pack('!BBBH', self.header_form, self.version_specific_bits, self.destination_connection_id, len(self.payload)) + self.payload
    
    def unpack_short(self, data):
        # Unpacks the byte stream into the object
        self.header_form, self.version_specific_bits, self.destination_connection_id, self.payload_length = struct.unpack('!BBBH', data[:4])
        self.payload = data[4:]

class QuicFrame:
    def __init__(self, type, data):
        self.type = type
        self.data = data

    def pack(self):
        return struct.pack('!B', self.type) + self.data

    def unpack(self, data):
        self.type = struct.unpack('!B', data[:1])
        self.data = data[1:]
# endregion

# region QUIC API

    

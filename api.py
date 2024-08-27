import time     
import socket       
import threading    # For handling multiple streams
import struct       # For packing and unpacking data


# Default values
BUFFER_SIZE = 65536                     # The buffer size is the maximum amount of data that can be received at once
DEFAULT_SERVER_HOST = "127.0.0.1"       # The default host for the server
DEFAULT_SERVER_PORT = 9997              # The default port for the server

# Constants
# Header types
LONG_HEADER = 1
SHORT_HEADER = 0

# Packet types
HANDSHAKE = 1
END_CONNECTION = 2
END_STREAM = 3
DATA = 4



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
    def __init__(self, source_id, destination_id, payload, stream_id, pos_in_stream):
        # Check if payload is a handshake, end connection or data packet
        if payload == "handshake":
            self.packet_type = HANDSHAKE
            self.header_form = LONG_HEADER                     # Header Form, long for handshake
        elif payload == "end":
            self.packet_type = END_CONNECTION
            self.header_form = LONG_HEADER                     # Header Form, long for end connection
        elif payload == "end_stream":
            self.packet_type = END_STREAM
            self.header_form = LONG_HEADER                     # Header Form, long for end stream
        else:
            self.packet_type = DATA
            self.header_form = SHORT_HEADER                    # Header Form, short for data packet
        # Long Header as suggested in RFC 8999 Section 5.1
        self.version_specific_bits = 0           # not used - Version-Specific Bits (7 bits)
        self.version = 0                         # not used - Version (32 bits)
        self.destination_connection_id_length = 0  # not used - Destination Connection ID Length (8 bits)
        self.destination_connection_id = 0      # Destination Connection ID (0..2040 bits, we set it to 1 bit to allow only 2 connection IDs)
        self.source_connection_id_length = 0      # not used - Source Connection ID Length (8 bits)
        self.source_connection_id = 0           # Source Connection ID (0..2040 bits, we set it to 1 bit to allow only 2 connection IDs)
        # self.version_specific_data = 0          # not used - Version-Specific Data (..)
        # TODO add stream ID?
        self.payload_length = len(payload)       # used instead of above comment, Payload Length (0..2^16-1, 16 bits)
        self.payload = payload                   # Payload (0..2^16-1)

        # TODO NEEDED?
        self.stream_id = stream_id
        self.pos_in_stream = pos_in_stream
    
    def __str__(self):
        return f"Packet Type: {self.packet_type_str()}, Header Form: {self.header_form_str()}, Destination Connection ID: {self.destination_connection_id}, Source Connection ID: {self.source_connection_id}, Payload Length: {self.payload_length}, Payload: {self.payload[:10]} ... {self.payload[-10:]}" 
    
    def sendto(self, sock, address):
        # Pack the packet and send it to the address
        # TODO encode?
        packed_packet = self.pack()
        sock.sendto(packed_packet, address)
        print(f"Stream {self.stream_id} - Packet #{self.pos_in_stream} sent to {address}: {self}")
    '''
    Packing and unpacking:
    !: represents network byte order (big-endian)
    B: unsigned char (1 byte - 8 bits)
    H: unsigned short (usually 2 bytes - 16 bits)
    I: unsigned int (usually 4 bytes - 32 bits)

    We do this because that our way to control the sizing of the fields in the packet in python, to minimize overhead
    '''
    def pack(self):
        # Checks header form to determine if it is a long header or a short header
        if self.header_form == LONG_HEADER:
            return self.pack_long()
        else:
            return self.pack_short()
    
    def unpack(self, data):
        # Checks header form to determine if it is a long header or a short header
        if data[0] == LONG_HEADER:
            self.unpack_long(data)
        else:
            self.unpack_short(data)

    ################################## Private helpers ##################################
    def __packet_type_str(self):
        if self.packet_type == HANDSHAKE:
            return "Handshake"
        elif self.packet_type == END_CONNECTION:
            return "End Connection"
        elif self.packet_type == END_STREAM:
            return "End Stream"
        else:
            return "Data"
    
    def __header_form_str(self):
        if self.header_form == LONG_HEADER:
            return "Long Header"
        else:
            return "Short Header"
        
    def __pack_long(self):
        self.header_form = LONG_HEADER      # make sure
        # Packs all the data into a byte stream
        return struct.pack('!BBIBBBBH', self.header_form, self.version_specific_bits, self.version, self.destination_connection_id_length, self.destination_connection_id, self.source_connection_id_length, self.source_connection_id, self.version_specific_data, len(self.payload)) + self.payload
    
    def __unpack_long(self, data):
        # Unpacks the byte stream into the object
        self.header_form, self.version_specific_bits, self.version, self.destination_connection_id_length, self.destination_connection_id, self.source_connection_id_length, self.source_connection_id, self.version_specific_data, self.payload_length = struct.unpack('!BBIBBBBH', data[:16])
        self.payload = data[16:]
        self.head_form = LONG_HEADER
        
    def __pack_short(self):
        self.header_form = SHORT_HEADER    # make sure
        # Packs only header_form, version_specific_bits, destination_connection_id, version_specific_data and payload
        return struct.pack('!BBBH', self.header_form, self.version_specific_bits, self.destination_connection_id, len(self.payload)) + self.payload
    
    def __unpack_short(self, data):
        # Unpacks the byte stream into the object
        self.header_form, self.version_specific_bits, self.destination_connection_id, self.payload_length = struct.unpack('!BBBH', data[:4])
        self.payload = data[4:]
        self.header_form = SHORT_HEADER
# endregion

# region QUIC API

    

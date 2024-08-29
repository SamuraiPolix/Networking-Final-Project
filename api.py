import time     
import socket       
import threading    # For handling multiple streams
import struct       # For packing and unpacking data


DEBUG = True

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
START_STREAM = 2
END_STREAM = 3
DATA = 4
ACK = 5
END_CONNECTION = 6



# ========================================================================
# =============================== QUIC API ===============================
# ========================================================================

# region QUIC Packet


class QuicPacket:
    def __init__(self, source_id, destination_id, payload, stream_id, pos_in_stream):
        # Long Header as suggested in RFC 8999 Section 5.1
        self.version_specific_bits = 0           # not used - Version-Specific Bits (7 bits)
        self.version = 0                         # not used - Version (32 bits)
        self.destination_connection_id_length = 1  # not used - Destination Connection ID Length (8 bits)
        self.destination_connection_id = destination_id      # Destination Connection ID (0..2040 bits, we set it to 1 bit to allow only 2 connection IDs)
        self.source_connection_id_length = 1      # not used - Source Connection ID Length (8 bits)
        self.source_connection_id = source_id           # Source Connection ID (0..2040 bits, we set it to 1 bit to allow only 2 connection IDs)
        # self.version_specific_data = 0          # not used - Version-Specific Data (..)
        self.stream_id = stream_id
        self.pos_in_stream = pos_in_stream
        self.payload_length = len(payload)       # used instead of above comment, Payload Length (0..2^16-1, 16 bits)
        self.payload = payload                   # Payload (0..2^16-1)
        if not isinstance(payload, bytes):
            self.non_binary_payload = payload
        else:
            self.non_binary_payload = self.payload.decode("utf-8")
        self.__set_packet_type()

    # def __init__(self):
    #     self.packet_type = 0
    #     self.header_form = 0
    #     self.version_specific_bits = 0
    #     self.version = 0
    #     self.destination_connection_id_length = 0
    #     self.destination_connection_id = 0
    #     self.source_connection_id_length = 0
    #     self.source_connection_id = 0
    #     self.version_specific_data = 0
    #     self.stream_id = 0
    #     self.pos_in_stream = 0
    #     self.payload_length = 0
    #     self.payload = ""

    def __set_packet_type(self):
        # Check if payload is a handshake, end connection or data packet
        
        if self.non_binary_payload == "handshake":
            self.packet_type = HANDSHAKE
            self.header_form = LONG_HEADER                     # Header Form, long for handshake
        elif self.non_binary_payload == "end":
            self.packet_type = END_CONNECTION
            self.header_form = LONG_HEADER                     # Header Form, long for end connection
        elif self.non_binary_payload == "end_stream":
            self.packet_type = END_STREAM
            self.header_form = LONG_HEADER                     # Header Form, long for end stream
        elif self.non_binary_payload[:3] == "ACK":
            self.packet_type = ACK
            self.header_form = SHORT_HEADER                    # Header Form, short for ack packet
        else:
            self.packet_type = DATA
            self.header_form = SHORT_HEADER                    # Header Form, short for data packet
    
    def __str__(self):
        return f"Packet Type: {self.__packet_type_str()}, Header Form: {self.__header_form_str()}, Destination Connection ID: {self.destination_connection_id}, Source Connection ID: {self.source_connection_id}, Stream ID: {self.stream_id}, Position in Stream: {self.pos_in_stream}, Payload Length: {self.payload_length}, Payload: {self.payload[:5]} ... {self.payload[-5:]}"
    
    def sendto(self, sock, address):
        # Pack the packet and send it to the address
        packed_packet = self.pack()
        sock.sendto(packed_packet, address)
        if DEBUG:
            print(f"Stream {self.stream_id} - Packet #{self.pos_in_stream} sent to {address}: {self}")

    def recvfrom(self, sock):
        # Receive the packet and unpack it
        data, address = sock.recvfrom(BUFFER_SIZE)
        self.unpack(data)
        if DEBUG:
            print(f"Received {self.__packet_type_str()} packet from {address}: {self}")
        return address
    
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
            return self.__pack_long()
        else:
            return self.__pack_short()
    
    def unpack(self, data):
        # Checks header form to determine if it is a long header or a short header
        if data[0] == LONG_HEADER:
            self.__unpack_long(data)
        else:
            self.__unpack_short(data)
        if not isinstance(self.payload, bytes):
            self.non_binary_payload = self.payload
        else:
            self.non_binary_payload = self.payload.decode("utf-8")
        self.__set_packet_type()

    ################################## Private helpers ##################################
    def __packet_type_str(self):
        if self.packet_type == HANDSHAKE:
            return "Handshake"
        elif self.packet_type == END_CONNECTION:
            return "End Connection"
        elif self.packet_type == END_STREAM:
            return "End Stream"
        elif self.packet_type == ACK:
            return "Ack"
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
        return struct.pack('!BBIBBBBBHH', self.header_form, self.version_specific_bits, self.version, self.destination_connection_id_length, self.destination_connection_id, self.source_connection_id_length, self.source_connection_id, self.stream_id, self.pos_in_stream, self.payload_length) + self.non_binary_payload.encode("utf-8")
    
    def __unpack_long(self, data):
        # Unpacks the byte stream into the object
        self.header_form, self.version_specific_bits, self.version, self.destination_connection_id_length, self.destination_connection_id, self.source_connection_id_length, self.source_connection_id, self.stream_id, self.pos_in_stream, self.payload_length = struct.unpack('!BBIBBBBBHH', data[:15])

        self.payload = data[15:]
        self.head_form = LONG_HEADER
        
    def __pack_short(self):
        self.header_form = SHORT_HEADER    # make sure
        # Packs only header_form, version_specific_bits, destination_connection_id, version_specific_data and payload
        return struct.pack('!BBBBHH', self.header_form, self.version_specific_bits, self.destination_connection_id, self.stream_id, self.pos_in_stream, self.payload_length) + self.non_binary_payload.encode("utf-8")
    
    def __unpack_short(self, data):
        # Unpacks the byte stream into the object
        self.header_form, self.version_specific_bits, self.destination_connection_id, self.stream_id, self.pos_in_stream, self.payload_length, = struct.unpack('!BBBBHH', data[:8])
        self.payload = data[8:]
        self.header_form = SHORT_HEADER
# endregion

def recv_packet(sock):
    # Receive the packet
    data, address = sock.recvfrom(BUFFER_SIZE)
    # Unpack the packet
    packet = QuicPacket(0, 0, "", 0, 0)
    packet.unpack(data)
    if DEBUG:
        print(f"Received packet from {address}: {packet}")
    return packet, address
    

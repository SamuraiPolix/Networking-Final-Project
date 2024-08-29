import argparse
import api
import socket
# import threading
import time

# Used assignment 2 as a reference for the server code

class Server:
    def __init__(self, server_address):
        self.server_address = server_address
        self.connection_id = 1  # Connection ID - using 1 bit in our implementation to allow only 2 connection IDs
        # Create a QUIC socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)      # UDP socket
        # allow the socket to be bound to an address that is already in use (if the server was restarted)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Assign address and port to the server's socket
        self.socket.bind(server_address)

        # Used to make sure only one thread can modify a shared data at the same time (the thread that "holds the lock")
        # self.lock = threading.Lock()

        self.run()

    ''' Moved printing stats to client.py, to calculate accurately even with packet loss
    def handle_client(self, quic_packet, client_address, stream_id):
        stream_id = quic_packet.stream_id
        
        if stream_id not in self.streams_data:
            self.streams_data[stream_id] = []

        self.streams_data[stream_id].append((quic_packet.pos_in_stream, quic_packet.non_binary_payload))

        # If the packet signals the end of the stream, save the file (for testing purposes)
        if quic_packet.packet_type == api.END_STREAM:
            # Set end time for the stream
            self.streams_stats[stream_id]['end_time'] = time.time()
            # data_rate, packet_rate = calculate_stats(start_time, bytes_received, packets_received)
            print(f"Stream {stream_id} completed:")
            print(f" - Bytes received: {self.streams_stats[stream_id]['bytes_received']}")
            print(f" - Packets received: {self.streams_stats[stream_id]['packets_received']}")
            # print(f" - Data rate: {data_rate:.2f} B/s")
            # print(f" - Packet rate: {packet_rate:.2f} packets/s")

            # self.save_file(stream_id)           # Not required

        else:   # add stats for the stream
            if stream_id not in self.streams_stats:
                self.streams_stats[stream_id] = {
                    'start_time': time.time(),      # Start time of the stream
                    'end_time': None,               # End time of the stream
                    'bytes_received': bytes_received,
                    'packets_received': packets_received
                }
            else:
                self.streams_stats[stream_id]['bytes_received'] += len(quic_packet.payload)
                self.streams_stats[stream_id]['packets_received'] += 1
    '''

    def run(self):
        print(f"Server running on {self.server_address[0]}:{self.server_address[1]}")
        socket.setdefaulttimeout(15)
        stream_id = 0
        while True:
            try:
                packet, client_address = api.recv_packet(self.socket)
            except socket.timeout:
                print("Socket timed out. Closing socket.")
                self.socket.close()
                break
            # ack = api.QuicPacket(0, 1, "ACK", packet.stream_id, packet.pos_in_stream)
            # with self.lock:
            #     ack.sendto(self.socket, client_address)
            # stream_id += 1
            # self.handle_client(packet, client_address, stream_id)
            # threading.Thread(target=self.handle_client, args=(packet, client_address, stream_id)).start()


    def save_file(self, stream_id):
        print(f"Saving stream {stream_id} to file...")
        # Sort packets by pos in stream (left value in dict)
        sorted_packets = sorted(self.streams_data[stream_id], key=lambda x: x[0])
        
        # Combine all the packets to form the complete file
        full_file_data = ""
        for _, packet in sorted_packets:
            full_file_data += packet

        # Assuming the file is a text file for testing purposes
        with open(f"received_file_{stream_id}.txt", "w") as f:
            f.write(full_file_data)

        print(f"Stream {stream_id} saved to file received_file_{stream_id}.txt")
        
        # # remove stream data from dict
        # del self.streams_data[stream_id]

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='A QUIC Server.')

    arg_parser.add_argument('-p', '--port', type=int,
                            default=api.DEFAULT_SERVER_PORT, help='The port to listen on.')
    arg_parser.add_argument('-H', '--host', type=str,
                            default=api.DEFAULT_SERVER_HOST, help='The host to listen on.')

    args = arg_parser.parse_args()

    host = args.host
    port = args.port

    Server((host, port))
import random
import threading
import string
import api
import socket
import argparse
import data_generator

# Used assignment 2 as a reference for the client code

# Generate packet size
PACKET_MIN_SIZE = 1000
PACKET_MAX_SIZE = 2000

def generate_payload_size():
    return random.randint(PACKET_MIN_SIZE, PACKET_MAX_SIZE)

class Client:
    def __init__(self, server_address):
        self.server_address = server_address
        self.connection_id = 0      # Connection ID - using 1 bit in our implementation to allow only 2 connection IDs
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)      # UDP socket
    
    def send_file(self, stream_id, file_path):
        payload_size = generate_payload_size()
        print(f"Stream {stream_id} using payload packet size: {payload_size} bytes")

        # Open in read binary mode to avoid encoding issues (allows for sending any file type, even images)
        with open(file_path, "rb") as f:
            while True:
                # Read a chunk and send it until there is no more data
                chunk = f.read(payload_size)
                if not chunk:   # No more data to read
                    break

                # Create packet and send it using api function
                packet = api.QuicPacket(self.connection_id, self.connection_id+1, chunk)
                packet.sendto(self.socket, self.server_address)

            # Finished sending the file, send a final packet with 0 length to signal the end of the stream

            # Create a final packet with 0 length and send it 
            
            print(f"Stream {stream_id} completed.")

        # Send a final packet to signal the end of the stream
        final_packet = struct.pack(PACKET_HEADER_FORMAT, stream_id, 0)
        sock.sendto(final_packet, SERVER_ADDRESS)

        print(f"Stream {stream_id} completed.")

    def run(self, file_paths):
        threads = []
        # Go over all files, "asigned" a stream ID to each file and start a thread to send the file
        for stream_id, file_path in enumerate(file_paths):
            thread = threading.Thread(target=self.send_file, args=(stream_id, file_path))
            thread.start()
            threads.append(thread)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="A QUIC Client.")

    arg_parser.add_argument("-p", "--port", type=int,
                            default=api.DEFAULT_SERVER_PORT, help="The port to connect to.")
    arg_parser.add_argument("-H", "-ip", "--host", type=str,
                            default=api.DEFAULT_SERVER_HOST, help="The host to connect to.")

    args = arg_parser.parse_args()

    host = args.host
    port = args.port

    client = Client((host, port))
    client.run(data_generator.generate_num_of_files(10))
    
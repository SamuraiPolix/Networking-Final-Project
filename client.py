import random
import threading
import string
import time
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
        # self.waiting_for_ack = {}   # Dict to store packets that are waiting for an ack

        self.lock = threading.Lock()
    
    def send_file(self, file_path, stream_id):        
        packet_size = generate_payload_size()
        bytes_sent = 0
        packets_sent = 0
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(packet_size)
                if not data:
                    break   # End of file
                quic_packet = api.QuicPacket(0, 1, data, stream_id, packets_sent)
                with self.lock:
                    time.sleep(0.0001)  # Wait for a second before sending the next packet
                    quic_packet.sendto(self.socket, self.server_address)
                    bytes_sent += len(data)
                    packets_sent += 1
                ''' Wrote to handle acks, ditched for now because it ruins performance and tests
                time.sleep(0.0001)  # Wait for a second before sending the next packet
                self.waiting_for_ack[(stream_id, packets_sent)] = quic_packet
                # wait for ack
                while (stream_id, packets_sent) in self.waiting_for_ack:
                    # Resend the packet if timeout occurs
                    with self.lock:
                        quic_packet.sendto(self.socket, self.server_address)
                    # time.sleep(1)  # Wait for a second before resending
                '''

        # Send a final packet to signal the end of the stream
        final_packet = api.QuicPacket(0, 1, "end_stream", stream_id, packets_sent)
        with self.lock:
            final_packet.sendto(self.socket, self.server_address)
        
        print(f"Stream {stream_id} completed: Sent {bytes_sent} bytes in {packets_sent} packets.")

    ''' Wrote to handle acks, ditched for now because it ruins performance and tests
    def receive_acks(self):
        while True:
            ack, _ = api.recv_packet(self.socket)
            if ack.packet_type == api.ACK:
                # remove from waiting for ack packets
                if (ack.stream_id, ack.pos_in_stream) in self.waiting_for_ack:
                    self.waiting_for_ack.pop((ack.stream_id, ack.pos_in_stream))
                print(f"Received ACK for stream {ack.stream_id} packet {ack.pos_in_stream}")
    '''

    def run(self, files):
        print(f"Client running on {self.server_address[0]}:{self.server_address[1]}")
        threads = []
        # Start a thread for each file and one for receiving acks
        for stream_id, file in enumerate(files):
            # Start a thread for each file to send it
            thread = threading.Thread(target=self.send_file, args=(file, stream_id+1))
            threads.append(thread)
            thread.start()
        
        ''' Wrote to handle acks, ditched for now because it ruins performance and tests
        # thread for receiving acks
        ack_thread = threading.Thread(target=self.receive_acks, args=())
        threads.append(ack_thread)    
        ack_thread.start()          
        '''                                            

        for thread in threads:
            thread.join()


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
    
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

NUM_OF_FILES = 10

def generate_payload_size():
    return random.randint(PACKET_MIN_SIZE, PACKET_MAX_SIZE)

class Client:
    def __init__(self, server_address):
        self.server_address = server_address
        self.connection_id = 0      # Connection ID - using 1 bit in our implementation to allow only 2 connection IDs
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)      # UDP socket
        # self.waiting_for_ack = {}   # Dict to store packets that are waiting for an ack

        self.streams_data = {}  # Dict to store file transfers by stream ID
        # store for each stream the number of packets and bytes received
        self.streams_stats = {}

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
                    # time.sleep(0.0001)  # Wait for a second before sending the next packet
                    quic_packet.sendto(self.socket, self.server_address)
                    bytes_sent += len(data)
                    packets_sent += 1
                    self.streams_data[stream_id] = []
                    self.streams_data[stream_id].append((quic_packet.pos_in_stream, quic_packet.non_binary_payload))

                    if stream_id not in self.streams_stats:
                        self.streams_stats[stream_id] = {
                                'start_time': time.time(),      # Start time of the stream
                                'end_time': None,               # End time of the stream
                                'bytes_sent': bytes_sent,
                                'packets_sent': packets_sent
                            }
                    else:       # add stats for the stream
                        self.streams_stats[stream_id]['bytes_sent'] += len(quic_packet.payload)
                        self.streams_stats[stream_id]['packets_sent'] += 1

                    
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

        # Set end time for the stream
        self.streams_stats[stream_id]['end_time'] = time.time()
        
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

        print("All files sent, printing stats...")

        time.sleep(2)
        
        print("=========== Stats: ===========")

        # Sort streams by stream ID and print in order
        sorted_streams = sorted(self.streams_stats.items(), key=lambda x: x[0])
        total_bytes_sent = 0
        total_packets_sent = 0
        avg_data_rate = 0
        avg_packet_rate = 0
        for stream_id, stats in sorted_streams:
            data_rate, packet_rate = calculate_stats(self.streams_stats[stream_id]['start_time'], self.streams_stats[stream_id]['end_time'], stats['bytes_sent'], stats['packets_sent'])
            print(f"Stream {stream_id}:")
            print(f" - Bytes sent: {stats['bytes_sent']:,}")
            print(f" - Packets sent: {stats['packets_sent']:,}")
            print(f" - Data rate: {data_rate:,.2f} B/s")
            print(f" - Packet rate: {packet_rate:,.2f} packets/s")
            print()
            total_bytes_sent += stats['bytes_sent']
            total_packets_sent += stats['packets_sent']
            avg_data_rate += data_rate
            avg_packet_rate += packet_rate

        avg_data_rate /= len(sorted_streams)
        avg_packet_rate /= len(sorted_streams)

        # print stats of all stream together
        print("=========== Total: ===========")
        print(f" - Total bytes sent: {total_bytes_sent:,}")
        print(f" - Total packets sent: {total_packets_sent:,}")
        print(f" - Average data rate: {avg_data_rate:,.2f} B/s")
        print(f" - Average packet rate: {avg_packet_rate:,.2f} packets/s")
        print()

        # Write average data rate and packet rate to a file, for graphing
        with open("client_stats.txt", "a") as file:
            file.write(f"{len(self.streams_stats)},{avg_data_rate},{avg_packet_rate}\n")
        
        self.socket.close()

def calculate_stats(start_time, end_time, bytes_received, packets_received):
    time_elapsed = end_time - start_time
    data_rate = bytes_received / time_elapsed
    packet_rate = packets_received / time_elapsed
    return data_rate, packet_rate

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="A QUIC Client.")

    arg_parser.add_argument("-p", "--port", type=int,
                            default=api.DEFAULT_SERVER_PORT, help="The port to connect to.")
    arg_parser.add_argument("-H", "-ip", "--host", type=str,
                            default=api.DEFAULT_SERVER_HOST, help="The host to connect to.")
    arg_parser.add_argument("-f", "--files", type=int,
                            default=NUM_OF_FILES, help="The number of files to generate and send, this is also the number of streams.")
    arg_parser.add_argument("-s", "--size", type=int,
                            default=data_generator.FILE_SIZE, help="The size of each file in MBs.")
    
    args = arg_parser.parse_args()

    host = args.host
    port = args.port
    data_generator.FILE_SIZE = args.size * 1024 * 1024

    # Remove all data_files to force generating new files
    data_generator.remove_files()

    client = Client((host, port))

    client.run(data_generator.generate_num_of_files(args.files))


    # Remove all data_files after sending
    data_generator.remove_files()


    
    
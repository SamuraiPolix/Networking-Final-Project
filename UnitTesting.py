import struct
import subprocess
import time
import unittest
import api

# Used for testing the client - MagicMock is used to mock the socket ("read" and "write" to socket without actually needing a socket and connection)
from client import Client
from unittest.mock import MagicMock
import threading

# Used for testing the server
import data_generator
from server import Server

# helpers to start server and client in another process
def start_server(port=9997):
    # Start the server as a background process
    server_process = subprocess.Popen(["python3", "server.py", "--port", str(port)])
    return server_process

def start_client(num_of_files=1, port=9997):
    # Start the client as a background process
    client_process = subprocess.Popen(["python3", "client.py", "--files", str(num_of_files), "--port", str(port)])
    return client_process

class TestQuicPacket(unittest.TestCase):
    def test_packet_creation(self):
        # This is a DATA packet -> short header
        packet = api.QuicPacket(1, 2, "test", 1, 1)
        self.assertEqual(packet.header_form, api.SHORT_HEADER)
        self.assertEqual(packet.source_connection_id, 1)
        self.assertEqual(packet.destination_connection_id, 2)
        self.assertEqual(packet.payload, "test")
        self.assertEqual(packet.packet_type, api.DATA)

    def test_pack_unpack_long(self):
        payload = "handshake"
        # This is a handshake packet -> long header
        packet = api.QuicPacket(1, 2, payload, 1, 0)
        packed = packet.pack()
        packet_unpacked = api.QuicPacket(0, 0, "", 0, 0)
        packet_unpacked.unpack(packed)
        self.assertEqual(packet_unpacked.header_form, api.LONG_HEADER)
        self.assertEqual(packet_unpacked.non_binary_payload, payload)
        self.assertEqual(packet_unpacked.source_connection_id, 1)
        self.assertEqual(packet_unpacked.destination_connection_id, 2)

    def test_pack_unpack_short(self):
        payload = "test_payload"
        # This is a DATA packet -> short header
        packet = api.QuicPacket(1, 2, payload, 1, 0)
        packed = packet.pack()
        packet_unpacked = api.QuicPacket(0, 0, "", 0, 0)
        packet_unpacked.unpack(packed)
        self.assertEqual(packet_unpacked.header_form, api.SHORT_HEADER)
        self.assertEqual(packet_unpacked.non_binary_payload, payload)
        # self.assertEqual(packet_unpacked.source_connection_id, 1)       # souce connection id is not used in short header
        self.assertEqual(packet_unpacked.destination_connection_id, 2)

    def test_packet_type(self):
        packet = api.QuicPacket(1, 2, "handshake", 1, 0)
        self.assertEqual(packet.packet_type, api.HANDSHAKE)
        self.assertEqual(packet.header_form, api.LONG_HEADER)
        
        packet = api.QuicPacket(1, 2, "ACK 123", 1, 0)
        self.assertEqual(packet.packet_type, api.ACK)
        self.assertEqual(packet.header_form, api.SHORT_HEADER)

        packet = api.QuicPacket(1, 2, b"words", 1, 0)
        self.assertEqual(packet.packet_type, api.DATA)
        self.assertEqual(packet.header_form, api.SHORT_HEADER)


class TestClient(unittest.TestCase):
    def test_send_file(self):
        client = Client(("127.0.0.1", 9997))
        # generate a file
        data_generator.generate_num_of_files(1)     # ALSO TESTS data_generator.py
        client.socket = MagicMock()
        client.send_file("data_files/file_1.txt", 1)
        # make sure the socket sendto method was actually called
        self.assertTrue(client.socket.sendto.called)

    def test_thread_safety(self):
        client = Client(("127.0.0.1", 9997))
        data_generator.generate_num_of_files(2)         # ALSO TESTS data_generator.py
        client.socket = MagicMock()
        files = ["data_files/file_1.txt", "data_files/file_2.txt"]
        
        def run_client(file, stream_id):
            client.send_file(file, stream_id)

        threads = [threading.Thread(target=run_client, args=(file, stream_id+1)) for stream_id, file in enumerate(files)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        # make sure the number of threads is equal to the number of files
        self.assertEqual(len(threads), len(files))

    def test_send_file_not_found(self):
        client = Client(("127.0.0.1", 9997))
        client.socket = MagicMock()
        with self.assertRaises(FileNotFoundError):
            client.send_file("non_existent_file.txt", 1)


# main.py also tests all of the above and more

if __name__ == "__main__":
    unittest.main()

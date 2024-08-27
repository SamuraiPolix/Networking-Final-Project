import argparse
import api
import socket
import threading

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

        print(f'Server is listening on {server_address[0]}:{server_address[1]}')

    def receive_data(self):
        while True:
            try:
                # "Establish connection with client."
                print("Waiting for client connection...")
                client_socket, address = server_socket.accept()

                print(f'Accepted connection from {address}')

                # Create a new thread to handle the client request (allowing multiple clients to connect)
                thread = threading.Thread(target=client_handler, args=(
                    client_socket, address))
                thread.start()
                threads.append(thread)
            except KeyboardInterrupt:
                print("Shutting down...")
                break

        for thread in threads:  # Wait for all threads to finish
            thread.join()

        while True:
            # Receive data from the client
            data, client_address = server_socket.recvfrom(1024)
            print(f'Received data from {client_address}')

            # Decode the data
            data = data.decode('utf-8')

            # Process the data
            response = api.process_request(data)

            # Send the response to the client
            server_socket.sendto(response.encode('utf-8'), client_address)
            print(f'Sent response to {client_address}')


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
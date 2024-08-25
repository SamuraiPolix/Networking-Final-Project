import argparse
import api
import socket

# Used assignment 2 as a reference for the server code

def server(host, port):
    # Create a QUIC socket
    # 'with' closes the socket when the "block" is exited
    # Create a new socket over IPv4 using UDP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        # allow the socket to be bound to an address that is already in use (if the server was restarted)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Assign address and port to the server's socket
        server_socket.bind((host, port))

        print(f'Server is listening on {host}:{port}')

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
        description='A Quic Server.')

    arg_parser.add_argument('-p', '--port', type=int,
                            default=api.DEFAULT_SERVER_PORT, help='The port to listen on.')
    arg_parser.add_argument('-H', '--host', type=str,
                            default=api.DEFAULT_SERVER_HOST, help='The host to listen on.')

    args = arg_parser.parse_args()

    host = args.host
    port = args.port

    server(host, port)
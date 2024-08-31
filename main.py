# This file is used to run everything and create graphs with the required data.
import subprocess
import time
import matplotlib.pyplot as plt

MIN_NUM_OF_FILES = 1
MAX_NUM_OF_FILES = 1

def start_server(port=9997):
    # Start the server as a background process
    server_process = subprocess.Popen(["python3", "server.py", "--port", str(port)])
    return server_process

def start_client(num_of_files=1, port=9997):
    # Start the client as a background process
    client_process = subprocess.Popen(["python3", "client.py", "--files", str(num_of_files), "--port", str(port)])
    return client_process

def main():
    for i in range(1, MAX_NUM_OF_FILES+1):
        # Start server
        server = start_server(9980+i)

        # wait for server to start
        time.sleep(1)

        print(f"Running test, with {i} files (streams)...")
        # Start client
        client = start_client(i, 9980+i)

        # Wait client to finish
        client.wait()

        # Optionally, wait for the server to finish (if it has a termination condition)
        server.terminate()
        server.wait()

        print(f"Test with {i} files completed...")
    
    # Generate graphs
    print("Generating graphs...")
    # client_stats.txt has all the stats in format: f"{NUM_OF_FILES},{avg_data_rate},{avg_packet_rate}\n"
 
    create_graphs_from_file("client_stats.txt")

def create_graphs_from_file(file):
    num_files_list = []
    avg_data_rate_list = []
    avg_packet_rate_list = []

    # read all stats from the file that client.py produced
    for line in open("client_stats.txt", "r"):
        num_files, avg_data_rate, avg_packet_rate = line.split(",")
        num_files_list.append(int(num_files))
        avg_data_rate_list.append(float(avg_data_rate))
        avg_packet_rate_list.append(float(avg_packet_rate))
    # Create graphs
    plt.figure()
    plt.scatter(num_files_list, avg_packet_rate_list, marker='o')
    plt.title("Average Packets per Second vs Number of Streams")
    plt.xlabel("Number of Streams")
    plt.ylabel("Average Packets per Second")
    plt.grid(True)
    plt.savefig(f"avg_packets_per_second.png")
    plt.show()

    plt.figure()
    plt.scatter(num_files_list, avg_data_rate_list, marker='o', color='r')
    plt.title("Average Data Rate (Bits) vs Number of Streams")
    plt.xlabel("Number of Streams")
    plt.ylabel("Average Data Rate (Bits)")
    plt.grid(True)
    plt.savefig(f"avg_data_rate.png")
    plt.show()

if __name__ == "__main__":
    main()
    # create_graphs_from_file("client_stats.txt")

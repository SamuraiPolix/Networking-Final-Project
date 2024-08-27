import os
import random
import string

FILES_FOLDER = "data_files"
# 10 MB
FILE_SIZE = 10 * 1024 * 1024


# Generate random data of a specific size, default size is 10 MB
def generate_random_data(data_size: int = FILE_SIZE):
    # Generate random characters to fill the data
    data = ''.join(random.choices(string.ascii_uppercase + string.digits, k=data_size))
    return data

# Generate a number of files with random data, default size is 10 MB per file
def generate_num_of_files(num_of_files, size_for_each_file: int = FILE_SIZE):
    # Make sure FILES_FOLDER exists
    if not os.path.exists(FILES_FOLDER):
        os.makedirs(FILES_FOLDER)
    files = []
    # Generate data and save it to files
    for i in range(num_of_files):
        data = generate_random_data(size_for_each_file)
        with open(f"{FILES_FOLDER}/file_{i}.txt", "w") as file:
            file.write(data)
        # Add the file to the list of files
        files.append(f"{FILES_FOLDER}/file_{i}.txt")
    return files
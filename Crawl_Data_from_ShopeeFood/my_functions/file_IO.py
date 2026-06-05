# Write file txt function
def write_file_txt(filename, list_data):
    import os
    # Create directory if it doesn't exist
    directory = os.path.dirname(filename)
    if directory:  # Only create if there's a directory path
        os.makedirs(directory, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        for item in list_data:
            f.write(item)


# Read file txt function
def read_file_txt(filename):
    import os
    # Note: We don't create directory for reading, file should already exist
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.rstrip("\n") for line in lines]

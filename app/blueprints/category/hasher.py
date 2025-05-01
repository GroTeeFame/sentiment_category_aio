import sys
import hashlib

def hash_file(filepath):
    # Create a hash object
    sha256_hash = hashlib.sha256()
    
    # Open the file in binary mode and read it in chunks
    try:
        with open(filepath, 'rb') as f:
            # Read the file in chunks to efficiently handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except FileNotFoundError:
        # If the file is not found, provide a clear error message
        print(f"Error: The file '{filepath}' does not exist.")
        return None
    except PermissionError:
        # Handle permission errors when attempting to open the file
        print(f"Error: Permission denied for file '{filepath}'.")
        return None
    
    # Get the hexadecimal digest of the hash
    return sha256_hash.hexdigest()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Ensure a file path is provided as a command-line argument
        print("Usage: python script.py <filepath>")
    else:
        filepath = sys.argv[1]
        file_hash = hash_file(filepath)
        if file_hash:
            print(f"The SHA-256 hash of the file is: {file_hash}")
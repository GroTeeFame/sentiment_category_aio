import sys
import hashlib
from flask import current_app

from app.logger_setup import setup_logger

logger = setup_logger(__name__)

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
        logger.error(f"Error: The file '{filepath}' does not exist.")
        return None
    except PermissionError:
        # Handle permission errors when attempting to open the file
        logger.error(f"Error: Permission denied for file '{filepath}'.")
        return None
    
    # Get the hexadecimal digest of the hash
    return sha256_hash.hexdigest()
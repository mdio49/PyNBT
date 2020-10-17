import nbt, os, gzip, io, time
from nbt.tags import TAG_Compound

class RegionFile:

    """
    Represents a file that is used to hold chunk data under the standard Minecraft region file format (.mca).
    """
    def __init__(self, path):
        self.__locations = [[0 for x in range(32)] for y in range(32)]
        self.__timestamps = [[0 for x in range(32)] for y in range(32)]
        self.__chunks = [[None for x in range(32)] for y in range(32)]

        # Create the file if it doesn't exist.
        if not os.path.exists(path):
            self.__fp = open(path, 'wb+')
            self.__fp.write(b'\x00' * 8192)
        else:
            self.__fp = open(path, 'rb+')
            self.__load_header()

    def __del__(self):
        if self.__fp is not None:
            self.__fp.close()

    def __enter__(self):
        return self

    def __exit__(sel, exc_type, exc_val, exc_tb):
        pass
    
    def __getitem__(self, key):
        if not isinstance(key, tuple):
            raise TypeError(f"Expected key of type 'tuple', not '{type(key).__name__}'.")
        if len(key) != 2:
            raise ValueError("Expected tuple with 2 elements.")
        return self.get_chunk(key[0], key[1])
    
    def __setitem__(self, key, value):
        if not isinstance(key, tuple):
            raise TypeError(f"Expected key of type 'tuple', not '{type(key).__name__}'.")
        if len(key) != 2:
            raise ValueError("Expected tuple with 2 elements.")
        if value is not None and not isinstance(value, TAG_Compound):
            raise TypeError(f"Expected value of type 'TAG_Compound', not '{type(value).__name__}'.'")
        self.set_chunk(key[0], key[1], value)

    def __iter__(self):
        self.__x = 0
        self.__z = 0
        return self
    
    def __next__(self):
        x = 0; z = 0; chunk = None
        while chunk is None:
            if self.__x >= 32:
                raise StopIteration
            x = self.__x; z = self.__z
            chunk = self.get_chunk(x, z)
            self.__z += 1
            if self.__z >= 32:
                self.__z = 0
                self.__x += 1
        return x, z, chunk
    
    def get_chunk(self, x, z):
        """Gets the chunk at position (x, z) in memory. Returns 'None' if the chunk is not loaded or is not present in the region file."""
        return self.__chunks[x][z]
    
    def set_chunk(self, x, z, chunk):
        """Sets the chunk at position (x, z) in memory. Note that this does not modify the region file on disk."""
        self.__chunks[x][z] = chunk
    
    def load_chunk(self, x, z):
        """Loads the chunk at position (x, z) into memory. Returns a TAG_Compound containing the chunk's data, or 'None' if the chunk is not present in the region file."""
        if self.__locations[x][z] == 0:
            return None
        
        # Locate the chunk in the region file.
        offset, size = self.__extract_loc(x, z)
        self.__fp.seek(4096 * offset)

        # Extract the chunk's data.
        length_bytes = self.__fp.read(4)
        length = int.from_bytes(length_bytes, byteorder='big', signed=False)
        compression = int.from_bytes(self.__fp.read(1), byteorder='big', signed=False)
        data = self.__fp.read(length - 1)

        # Decompress the data (if required).
        if compression == 1:
            data = gzip.decompress(data)
        elif compression == 2:
            data = gzip.zlib.decompress(data)
        
        # Extract the chunk data into a compound tag.
        fp = io.BytesIO(data)
        chunk = TAG_Compound.load(None, fp)

        # Store the chunk data in memory.
        self.__chunks[x][z] = chunk['']

        # Return the loaded chunk for convenience.
        return self.__chunks[x][z]

    def unload_chunk(self, x, z):
        """Unloads the chunk at position (x, z) from memory."""
        self.__chunks[x][z] = None
    
    def delete_chunk(self, x, z):
        """Deletes the chunk at position (x, z) from the disk."""
        if self.__locations[x][z] == 0:
            return
        
        # Update the chunk's header.
        offset, old_size = tuple(x * 4096 for x in self.__extract_loc(x, z))
        self.__resize_chunk(x, z, 0)

        # Delete the chunk from the region file on the disk.
        self.__fp.seek(offset + old_size)
        after = self.__fp.read()
        self.__fp.seek(offset)
        self.__fp.write(after)
        self.__fp.truncate()
    
    def save_chunk(self, x, z, compression='zlib'):
        """Saves the chunk at position (x, z) to the disk (only if the chunk is present in memory)."""
        if self.__chunks[x][z] is None:
            return
        
        with io.BytesIO() as fp:
            # Get the chunk data.
            chunk = TAG_Compound('')
            chunk.add(self.__chunks[x][z])
            data = chunk.payload()

            # Compress the data if necessary.
            compression_id = 3
            if compression == 'gzip':
                data = gzip.compress(data)
                compression_id = 1
            elif compression == 'zlib':
                data = gzip.zlib.compress(data)
                compression_id = 2
            elif compression != 'none':
                raise ValueError("Invalid compression type specified.")
            
            # Write the data to the stream.
            length = len(data) + 1
            fp.write(length.to_bytes(4, byteorder='big', signed=False))
            fp.write(compression_id.to_bytes(1, byteorder='big', signed=False))
            fp.write(data)

            # Pad the chunk so it's a multiple of 4096 bytes.
            bytes_written = fp.tell()
            if bytes_written % 4096 != 0:
                padding = b'\x00' * (4096 - (bytes_written % 4096))
                fp.write(padding)
            
            # Initialize the chunk's header if it's not present in the file.
            if self.__locations[x][z] == 0:
                self.__init_chunk(x, z)
            
            # Update the chunk's header.
            offset, old_size = tuple(x * 4096 for x in self.__extract_loc(x, z))
            self.__resize_chunk(x, z, int(fp.tell() / 4096))
            
            # Rewrite the file to accommodate for the new chunk.
            self.__fp.seek(offset + old_size)
            after = self.__fp.read()
            self.__fp.seek(offset)
            self.__fp.write(fp.getvalue())
            self.__fp.write(after)
            self.__fp.truncate()

    def load_all(self):
        """Loads all chunks into memory."""
        for z in range(32):
            for x in range(32):
                self.load_chunk(x, z)
            
    def unload_all(self):
        """Unloads all loaded chunks from memory."""
        for z in range(32):
            for x in range(32):
                self.__chunks[x][z] = None

    def save_all(self, compression='zlib'):
        """Saves all loaded chunks to the disk."""
        for z in range(32):
            for x in range(32):
                self.save_chunk(x, z, compression=compression)

    def __load_header(self):
        self.__fp.seek(0)

        # Read locations.
        for z in range(32):
            for x in range(32):
                self.__locations[x][z] = int.from_bytes(self.__fp.read(4), byteorder='big', signed=False)

        # Read timestamps.
        for z in range(32):
            for x in range(32):
                self.__timestamps[x][z] = int.from_bytes(self.__fp.read(4), byteorder='big', signed=False)

    def __extract_loc(self, x, z):
        offset = self.__locations[x][z] >> 8
        size = self.__locations[x][z] & 0xFF
        return offset, size
    
    def __init_chunk(self, x, z):
        self.__fp.seek(0, 2)
        self.__locations[x][z] = int(self.__fp.tell() / 4096) << 8

    def __resize_chunk(self, x, z, size):
        offset, old_size = self.__extract_loc(x, z)
        self.__locations[x][z] = (offset << 8) + size if size > 0 else 0
        self.__timestamps[x][z] = int(time.time())
        
        # Update the header for chunk (x, z).
        self.__fp.seek(4 * ((x % 32) + (z % 32) * 32))
        self.__fp.write(self.__locations[x][z].to_bytes(4, byteorder='big', signed=False))
        self.__fp.seek(4096, 1)
        self.__fp.write(self.__timestamps[x][z].to_bytes(4, byteorder='big', signed=False))

        # Update the offset for chunks positioned after this chunk in the file.
        self.__fp.seek(0)
        size_change = size - old_size
        for z1 in range(32):
            for x1 in range(32):
                cur_offset, cur_size = self.__extract_loc(x1, z1)
                if cur_offset > offset:
                    self.__locations[x1][z1] = ((cur_offset + size_change) << 8) + cur_size
                    self.__fp.write(self.__locations[x1][z1].to_bytes(4, byteorder='big', signed=False))
                else:
                    self.__fp.seek(4, 1)

import os, io, gzip
from nbt.tags import TAG_Compound

class NBTFile:
    
    """
    Represents a file that is used to hold NBT data, containing a single root compound
    tag that can be used to modify the tags within the file.
    
    The file is automatically opened at the given path, and will be closed dynamically
    when the NBTFile object is destroyed. The 'mode' argument is optional, and can be
    used to specify how the file is opened (the default is 'modify').
    - create:   Opens the file for writing, creating a new file and overwriting the contents of
                the current file at the path if it already exists.
    - load      Opens the file for reading, loading the NBT data from the current file. Raises a
                FileNotFoundError if the file does not exist.
    - modify:   Opens the file for reading and writing. If the file already exists, then the NBT
                data is loaded into the current NBTFile instance.
    """
    def __init__(self, path, mode='modify', compress=True):
        self.__fp = None
        self.__compress = compress
        if mode == 'create':
            self.__fp = open(path, "wb")
            self.__root = TAG_Compound(None)
        elif mode == 'load':
            self.__fp = open(path, "rb")
            self.load()
        elif mode == 'modify':
            if not os.path.exists(path):
                self.__fp = open(path, "wb+")
            else:
                self.__fp = open(path, "rb+")
                self.load()
        else:
            raise ValueError("Invalid mode specified.")
    
    def __del__(self):
        if self.__fp is not None:
            self.__fp.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __str__(self):
        return str(self.root)

    @property
    def root(self):
        """The root compound tag."""
        return self.__root
    
    def copy(self, path):
        """Creates a copy of the current NBTFile instance at a different location with the same tags."""
        file = NBTFile(path, mode='create', compress=self.__compress)
        file.__root = deepcopy(self.root)
        file.save()
        return file

    def save(self):
        """Saves the NBT data to the disk."""
        self.__fp.truncate(0)
        payload = self.__root.payload()
        if self.__compress:
            payload = gzip.compress(payload)
        self.__fp.write(payload)
    
    def load(self):
        self.__fp.seek(0)
        data = self.__fp.read()
        if self.__compress:
            data = gzip.decompress(data)
        fp = io.BytesIO(data)
        self.__root = TAG_Compound.load(None, fp)

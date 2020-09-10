import nbt.tags, sys, inspect, struct
from copy import copy, deepcopy
from nbt.NBTTag import NBTTag

class TAG_Compound(NBTTag):

    """
    Represents an unordered collection of named binary tags.    
    """
    def __init__(self, name):
        super().__init__(name, None)
        self.__tags = []

    def __getitem__(self, key):
        tag = self.get(key)
        if tag is None:
            raise IndexError("A tag with the indexed name does not exist in the compound.")
        return tag.value

    def __setitem__(self, key, value):
        tag = self.get(key)
        if tag is None:
            raise IndexError("A tag with the indexed name does not exist in the compound.")
        tag.value = value
    
    def __iter__(self):
        return self.__tags.__iter__()

    def __next__(self):
        return self.__tags.__next__()
    
    def __len__(self):
        return len(self.__tags)
    
    def __str__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        if type(self) != type(other):
            return False
        if self.name != other.name:
            return False
        if len(self.__tags) != len(other.__tags):
            return False
        for A in self.__tags:
            found = False
            for B in other.__tags:
                if A == B:
                    found = True
                    break
            if not found:
                return False
        return True
        
    def __contains__(self, item):
        if isinstance(item, str):
            return self.get(item) is not None
        elif isinstance(item, tuple):
            if len(item) != 2:
                return False
            tag = self.get(item[0])
            return tag.value == item[1] if tag is not None else False
        return False
        
    @property
    def value(self):
        return self

    def validate(self, value):
        pass
    
    @classmethod
    def get_id(cls):
        return 10
    
    def payload(self):
        data = b''
        for tag in self.__tags:
            data += tag.get_id().to_bytes(1, byteorder='big', signed=False)
            data += len(tag.name).to_bytes(2, byteorder='big', signed=False)
            data += tag.name.encode(encoding='UTF-8')
            data += tag.payload()
        data += b'\x00'
        return data

    @classmethod
    def load(cls, name, fp):
        compound = cls(name)
        while True:
            # Get the tag type.
            type_id = int.from_bytes(fp.read(1), byteorder='big', signed=False)
            if type_id == 0:
                break
            
            # Extract the name of the tag.
            name_len = int.from_bytes(fp.read(2), byteorder='big', signed=False)
            tag_name = str(fp.read(name_len), encoding='UTF-8')

            # Load data for the tag's value.
            tag_type = nbt.tags.get_tag_type(type_id)
            if tag_type is None:
                raise IOError(f"Invalid tag type ID: {type_id}")
            tag = tag_type.load(tag_name, fp)

            # Append the tag to the compound.
            compound.add(tag)
        
        return compound
    
    def add(self, tag, replace=False):
        """Adds the given tag to the compound. If 'replace' is false, then throws a """
        if not issubclass(type(tag), NBTTag):
            raise TypeError(f"An object of type '{type(tag).__name__}' is not a valid NBT tag.")
        
        i = 0
        for x in self.__tags:
            if x.name == tag.name:
                if not replace:
                    raise ValueError("A tag with the same name already exists in the compound.")
                self.__tags.remove(x)
                break
            i += 1
        self.__tags.insert(i, tag)
    
    def merge(self, source, mode='merge', recursive=True):
        """
        Copies tags from the given compound tag to the current compound. If 'recursive' is True, then the function
        will recurse for compound tags that are present in both the source and current compound. The 'mode' argument
        is optional and specifies how the tags will be merged into the compound (defaults to 'merge').
        - keep:     Only copies tags from the source that are not already present in the current compound.
        - merge:    Copies over all tags from the source and updates the values of tags in the current compound
                    that share the same name. Raises a TypeError if there are tags with inconsistent types.
        - replace:  Copies over all tags from the source, completely replacing any tags with duplicate names.
                    Raises a TypeError if the source compound contains tags of type TAG_Generic.
        - update:   Only updates tags in the current compound that are also present in the source with the same
                    name. Raises a TypeError if there are tags with inconsistent types.
        """
        if not isinstance(source, TAG_Compound):
            raise TypeError("Source tag must be of type TAG_Compound.")
        
        for tag in source:
            current = self.get(tag.name)
            if current is not None:
                if recursive and isinstance(tag, nbt.tags.TAG_Compound) and isinstance(current, nbt.tags.TAG_Compound):
                    self[tag.name].merge(tag, mode=mode, recursive=True)
                elif mode != 'keep':
                    if mode == 'replace':
                        self.add(deepcopy(tag), replace=True)
                    elif type(tag) != type(current):
                        raise TypeError(f"Inconsistent tag types: {type(tag).__name__} and {type(current).__name__}")
                    elif type(tag) == nbt.tags.TAG_Compound:
                        self[tag.name].__tags = deepcopy(tag.__tags)
                    elif type(tag) == nbt.tags.TAG_List:
                        self[tag.name].clear()
                        self[tag.name].extend(deepcopy(tag))
                    else:
                        self[tag.name] = tag.value
            elif mode != 'update':
                self.add(deepcopy(tag))

    def get(self, name):
        """Gets the tag in the compound with the given name, or None if the tag doesn't exist."""
        return next((x for x in self.__tags if x.name == name), None)
    
    def contains(self, tags : dict):
        """
        Tests if the compound contains the data in the given dictionary. If 'None' is used as a value
        for an item in the dictionary, then the tag may hold any value (i.e. only the name is checked).
        """
        if not isinstance(tags, dict):
            return False

        match = True
        for name, value in tags.items():
            tag = self.get(name) 
            if tag is not None and value is None:
                continue
            elif isinstance(tag, nbt.tags.TAG_Compound) or isinstance(tag, nbt.tags.TAG_List):
                match = tag.contains(value)
            elif tag is None or tag.value != value:
                match = False
            if not match:
                break

        return match

    def remove(self, name):
        """Removes the tag with the given name from the compound (if it exists)"""
        tag = self.get(name)
        if tag is not None:
            self.__tags.remove(tag)

    def clear(self):
        """Clears all tags from the compound."""
        self.__tags.clear()

    def to_dict(self):
        """Converts the compound tag into a Python dictionary."""
        result = {}
        for tag in self.__tags:
            if isinstance(tag, nbt.tags.TAG_Compound):
                result[tag.name] = tag.to_dict()
            elif isinstance(tag, nbt.tags.TAG_List):
                result[tag.name] = tag.to_array()
            else:
                result[tag.name] = tag.value
        return result
    
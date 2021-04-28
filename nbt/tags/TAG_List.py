import nbt.tags
from nbt.NBTTag import NBTTag

class TAG_List(NBTTag):

    """
    Represents an ordered list of named binary tags of the same tag type.
    """
    def __init__(self, name, list_type):
        if list_type is not None and not issubclass(list_type, NBTTag):
            raise ValueError("List type must be inheritable from NBTTag.")
        self.__type = list_type
        self.__tags = []
        super().__init__(name, None)
    
    def __getitem__(self, key):
        if isinstance(key, int):
            tag = self.__tags[key]
            return tag.value
        elif isinstance(key, slice):
            slice_str = f"{key.start if key.start is not None else ''}:{key.stop if key.stop is not None else ''}{':' + str(key.step) if key.step is not None else ''}"
            tags = TAG_List(self.name + f"[{slice_str}]", self.__type)
            tags.extend(self.__tags[key])
            return tags
        elif isinstance(key, dict):
            if self.__type is not None and self.__type != nbt.tags.TAG_Compound:
                raise TypeError("Dictionary indexing is only supported for lists with elements of type TAG_Compound.")
            matches = TAG_List(self.name + f"[{key}]", self.__type)
            for tag in self.__tags:
                if tag.contains(key):
                    matches.append(tag)
            return matches
        raise TypeError(f"Expected key of type 'int', 'slice', or 'dict'; not '{type(key).__name__}'.")
    
    def __setitem__(self, key, value):
        self.__tags[key].value = value

    def __delitem__(self, key):
        if isinstance(key, (int, slice)):
            del self.__tags[key]
        elif isinstance(key, dict):
            if self.__type is not None and self.__type != nbt.tags.TAG_Compound:
                raise TypeError("Dictionary indexing is only supported for lists with elements of type TAG_Compound.")
            for tag in self.__tags:
                if tag.contains(key):
                    self.__tags.remove(tag)
        else:
            raise TypeError(f"Expected key of type 'int', 'slice', or 'dict'; not '{type(key).__name__}'.")

    def __iter__(self):
        self.__i = 0
        return self

    def __next__(self):
        if self.__i >= len(self.__tags):
            raise StopIteration
        value = self.__tags[self.__i].value
        self.__i += 1
        return value

    def __len__(self):
        return len(self.__tags)
    
    def __str__(self):
        return '[' + ','.join(f'{tag}' for tag in self.__tags) + ']'

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        if type(self) != type(other):
            return False
        if self.name != other.name:
            return False
        if self.__type != other.__type:
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
        return item in [x.value for x in self.__tags]
    
    @property
    def value(self):
        return self
    
    def validate(self, value):
        pass
    
    @classmethod
    def get_id(cls):
        return 9
    
    def payload(self):
        type_id = self.__type.get_id() if self.__type is not None else 0
        data = nbt.tags.TAG_Byte(None, type_id).payload()
        data += nbt.tags.TAG_Int(None, len(self.__tags)).payload()
        for tag in self.__tags:
            data += tag.payload()
        return data
    
    @classmethod
    def load(cls, name, fp):
        type_id = nbt.tags.TAG_Byte.load(None, fp).value
        length = nbt.tags.TAG_Int.load(None, fp).value
        tag = cls(name, nbt.tags.get_tag_type(type_id))
        tag.__tags = [None] * length
        for i in range(0, length):
            tag.__tags[i] = tag.__type.load(None, fp)
        return tag

    def append(self, item):
        self.insert(len(self.__tags), item)
    
    def prepend(self, item):
        self.insert(0, item)
    
    def insert(self, index, item):
        # If the list type is not defined, then set it based on the type of the tag that is first inserted into the list.
        if self.__type is None:
            if not issubclass(type(item), NBTTag):
                raise TypeError(f"Dynamic tag initialization is not supported when list type is not defined.")
            self.__type = type(item)
        
        # Insert the item into the list depending on whether a tag or value was inputted.
        if isinstance(item, self.__type):
            self.__tags.insert(index, item)
        elif issubclass(type(item), NBTTag):
            raise TypeError(f"Value of type {type(item).__name__} does not match list type {self.__type.__name__}.")
        elif self.__type == nbt.tags.TAG_List or self.__type == nbt.tags.TAG_Compound:
            raise TypeError(f"Dynamic tag initialization is not supported for lists of type {self.__type.__name__}.")
        else:
            self.__tags.insert(index, self.__type(None, item))
    
    def extend(self, items):
        i = len(self.__tags)
        for x in items:
            self.insert(i, x)
            i += 1

    def contains(self, array : list) -> bool:
        """Tests if each element in the given array can be uniquely mapped to an element in the list tag."""
        if not isinstance(array, list):
            return False

        used_i = []; used_j = []
        for i in range(0, len(array)):
            if i in used_i:
                continue
            for j in range(0, len(self.__tags)):
                if j in used_j:
                    continue
                match = False
                if self.__type == nbt.tags.TAG_Compound or self.__type == nbt.tags.TAG_List:
                    if self.__tags[j].contains(array[i]):
                        match = True
                elif self.__tags[j].value == array[i]:
                    match = True
                if match == True:
                    used_i.append(i)
                    used_j.append(j)
                    break
 
        return len(used_i) == len(array)
    
    def clear(self):
        """Clears all tags from the list."""
        self.__tags.clear()
    
    def to_array(self) -> list:
        """Converts the list tag into a Python array."""
        result = []
        for tag in self.__tags:
            if isinstance(tag, nbt.tags.TAG_Compound):
                result.append(tag.to_dict())
            elif isinstance(tag, nbt.tags.TAG_List):
                result.append(tag.to_array())
            else:
                result.append(tag.value)
        return result

from abc import ABC, abstractmethod, abstractclassmethod

class NBTTag(ABC):

    def __init__(self, name, value):
        self.name = name
        self.__value = value
        self.validate(value)
    
    def __str__(self):
        return str({ self.name: self.value })

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        if type(self) != TAG_Generic and type(other) != TAG_Generic and type(self) != type(other):
            return False
        if self.name != other.name:
            return False
        return self.value == other.value

    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, value):
        self.validate(value)
        self.__value = value

    @abstractmethod
    def validate(self, value):
        """Validates the value of the tag to make sure its type is correct."""
        pass

    @abstractclassmethod
    def get_id(cls) -> int:
        """A single byte that uniquely identifies the tag type."""
        pass

    @abstractmethod
    def payload(self) -> str:
        """Converts the value of the tag into a byte array."""
        pass

    @abstractclassmethod
    def load(cls, name, fp):
        """Creates a new instance of the tag by reading data from the given bitstream."""
        pass

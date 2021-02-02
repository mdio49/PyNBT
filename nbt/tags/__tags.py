import struct
from abc import ABC, abstractmethod, abstractclassmethod
from nbt.NBTTag import NBTTag

class NBTTag_Integer(NBTTag, ABC):

    def __init__(self, name, value, min_value, max_value, suffix=''):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(name, value)
        self.suffix = suffix
    
    def __str__(self):
        return f'{self.value}{self.suffix}'
    
    def validate(self, value):
        if not isinstance(value, int) or not (value >= self.min_value and value <= self.max_value):
            raise TypeError(f"Expected integer value between {self.min_value} and {self.max_value}.")

class NBTTag_Array(NBTTag, ABC):

    def __init__(self, name, value, prefix):
        super().__init__(name, value)
        self.prefix = prefix
    
    def __str__(self):
        return f"[{self.prefix};{','.join(str(x) for x in self.value)}]"

    @abstractclassmethod
    def array_type(cls):
        pass

    def validate(self, value):
        if not isinstance(value, list):
            raise TypeError(f"Expected list value.")
        for x in value:
            self.array_type()(None, x)
    
    def payload(self):
        data = TAG_Int(None, len(self.value)).payload()
        for byte in self.value:
            data += self.array_type()(None, byte).payload()
        return data

    @classmethod
    def load(cls, name, fp):
        length = TAG_Int.load(None, fp).value
        value = [0] * length
        for i in range(0, length):
            value[i] = cls.array_type().load(None, fp).value
        return cls(name, value)

class TAG_Byte(NBTTag_Integer):

    def __init__(self, name, value):
        super().__init__(name, value, -128, 127, suffix='b')
    
    @classmethod
    def get_id(cls):
        return 1
    
    def payload(self):
        return self.value.to_bytes(1, byteorder='big', signed=True)
    
    @classmethod
    def load(cls, name, fp):
        value = int.from_bytes(fp.read(1), byteorder='big', signed=True)
        return cls(name, value)

class TAG_Short(NBTTag_Integer):

    def __init__(self, name, value):
        super().__init__(name, value, -32768, 32767, suffix='s')
    
    @classmethod
    def get_id(cls):
        return 2

    def payload(self):
        return self.value.to_bytes(2, byteorder='big', signed=True)
    
    @classmethod
    def load(cls, name, fp):
        value = int.from_bytes(fp.read(2), byteorder='big', signed=True)
        return cls(name, value)

class TAG_Int(NBTTag_Integer):

    def __init__(self, name, value):
        super().__init__(name, value, -2147483648, 2147483647)
    
    @classmethod
    def get_id(cls):
        return 3
    
    def payload(self):
        return self.value.to_bytes(4, byteorder='big', signed=True)
    
    @classmethod
    def load(cls, name, fp):
        value = int.from_bytes(fp.read(4), byteorder='big', signed=True)
        return cls(name, value)

class TAG_Long(NBTTag_Integer):

    def __init__(self, name, value):
        super().__init__(name, value, -9223372036854775808, 9223372036854775807, suffix='L')

    @classmethod
    def get_id(cls):
        return 4

    def payload(self):
        return self.value.to_bytes(8, byteorder='big', signed=True)
    
    @classmethod
    def load(cls, name, fp):
        value = int.from_bytes(fp.read(8), byteorder='big', signed=True)
        return cls(name, value)

class TAG_Float(NBTTag):

    def __init__(self, name, value):
        super().__init__(name, value)

    def __str__(self):
        return f'{self.value}f'

    def validate(self, value):
        if not isinstance(value, (float, int)):
            raise TypeError(f"Expected decimal value.")

    @classmethod
    def get_id(cls):
        return 5
    
    def payload(self):
        return struct.pack(">f", self.value)

    @classmethod
    def load(cls, name, fp):
        value = float(struct.unpack(">f", fp.read(4))[0])
        return cls(name, value)

class TAG_Double(NBTTag):

    def __init__(self, name, value):
        super().__init__(name, value)

    def __str__(self):
        return f'{self.value}d' if self.value.is_integer() else f'{self.value}'
    
    def validate(self, value):
        if not isinstance(value, (float, int)):
            raise TypeError(f"Expected decimal value.")

    @classmethod
    def get_id(self):
        return 6
    
    def payload(self):
        return struct.pack(">d", self.value)

    @classmethod
    def load(cls, name, fp):
        value = float(struct.unpack(">d", fp.read(8))[0])
        return cls(name, value)

class TAG_Byte_Array(NBTTag_Array):

    def __init__(self, name, value):
        super().__init__(name, value, 'B')
    
    @classmethod
    def array_type(cls):
        return TAG_Byte
        
    @classmethod
    def get_id(cls):
        return 7

class TAG_String(NBTTag):

    def __init__(self, name, value):
        super().__init__(name, value)
    
    def __str__(self):
        return f'"{self.value}"'

    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Expected string value.")
    
    @classmethod
    def get_id(self):
        return 8
    
    def payload(self):
        text = self.value.encode(encoding='UTF-8')
        return TAG_Short(None, len(text)).payload() + text
    
    @classmethod
    def load(cls, name, fp):
        length = TAG_Short.load(None, fp).value
        value = str(fp.read(length), encoding='UTF-8')
        return cls(name, value)

class TAG_Int_Array(NBTTag_Array):

    def __init__(self, name, value):
        super().__init__(name, value, 'I')
    
    @classmethod
    def array_type(cls):
        return TAG_Int
    
    @classmethod
    def get_id(cls):
        return 11

class TAG_Long_Array(NBTTag_Array):

    def __init__(self, name, value):
        super().__init__(name, value, 'L')
    
    @classmethod
    def array_type(cls):
        return TAG_Long
    
    @classmethod
    def get_id(cls):
        return 12

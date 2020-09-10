from nbt.tags.TAG_Compound import TAG_Compound
from nbt.tags.TAG_List import TAG_List
from nbt.tags.__tags import TAG_Byte
from nbt.tags.__tags import TAG_Byte_Array
from nbt.tags.__tags import TAG_Double
from nbt.tags.__tags import TAG_Float
from nbt.tags.__tags import TAG_Int
from nbt.tags.__tags import TAG_Int_Array
from nbt.tags.__tags import TAG_Long
from nbt.tags.__tags import TAG_Long_Array
from nbt.tags.__tags import TAG_Short
from nbt.tags.__tags import TAG_String

__TAG_TYPES = [
    TAG_Byte,
    TAG_Byte_Array,
    TAG_Compound,
    TAG_Double,
    TAG_Float,
    TAG_Int,
    TAG_Int_Array,
    TAG_List,
    TAG_Long,
    TAG_Long_Array,
    TAG_Short,
    TAG_String
]

def get_tag_type(type_id):
    """Gets the tag type associated with the given numerical ID, or None if it doesnt exist."""
    return next((x for x in __TAG_TYPES if x.get_id() == type_id), None)

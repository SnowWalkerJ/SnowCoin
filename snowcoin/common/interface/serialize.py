import struct
import collections
import warnings
from typing import Sequence, List, Tuple, NamedTuple


BYTES_ORDER = "<"


class SerializableAttribute:
    __slots__ = ['name', 'type_', 'readonly', 'serializer']
    def __init__(self, name, type_, readonly=False):
        self.name = name
        self.type_ = type_
        self.readonly = readonly
        self.serializer = get_serializer(type_)
        
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, "_{}".format(self.name))

    def __set__(self, obj, value):
        if self.readonly:
            raise TypeError("Attribute {} is read only".format(self.name))
        setattr(obj, "_{}".format(self.name), value)


class SerializableMeta(type):
    def __new__(cls, name, parent, members):
        mappings = []
        for member, attribute in members.items():
            if isinstance(attribute, SerializableAttribute):
                mappings.append((member, attribute.serializer))
        members['mappings'] = sorted(mappings)
        init_func = members.get('__init__')
        def init(self, *args, **kwargs):
            for key, _ in mappings:
                setattr(self, "_{}".format(key), kwargs.pop(key, None))
            if init_func:
                init_func(self, *args, **kwargs)
        members['__init__'] = init
        new_class = super(SerializableMeta, cls).__new__(cls, name, parent, members)
        new_class.serializer = CustomSerializer(new_class)
        return new_class


class Serializer:
    def serialize(self, value):
        raise NotImplementedError

    def deserialize(self, buffer):
        raise NotImplementedError


class BasicSerializer(Serializer):
    def __init__(self, fmt):
        self.fmt = fmt

    def serialize(self, value):
        return struct.pack("{}{}".format(BYTES_ORDER, self.fmt), value)

    def deserialize(self, buffer):
        size = struct.calcsize("{}{}".format(BYTES_ORDER, self.fmt))
        value = struct.unpack("{}{}".format(BYTES_ORDER, self.fmt), buffer[:size])[0]
        return value, buffer[size:]


class BytesSerializer(Serializer):
    def serialize(self, value):
        n = len(value)
        fmt = "{}L{}s".format(BYTES_ORDER, n)
        return struct.pack(fmt, n, value)

    def deserialize(self, buffer):
        fmt = "{}L".format(BYTES_ORDER)
        size = struct.calcsize(fmt)
        n = struct.unpack(fmt, buffer[:size])[0]
        buffer = buffer[size:]
        fmt = "{}{}s".format(BYTES_ORDER, n)
        size = struct.calcsize(fmt)
        value, buffer = struct.unpack(fmt, buffer[:size])[0], buffer[size:]
        return value, buffer


class SequenceSerializer(Serializer):
    type_mapping = {
        int: "L",
        float: "d",
    }
    def __init__(self, container_type, element_type):
        if not issubclass(container_type, (List, Tuple, NamedTuple)):
            raise TypeError("Can only serialize list/tuple/namedtuple type")
        if not issubclass(element_type, (int, float, bytes, Serializable)):
            raise TypeError("Can only serialize int/float/bytes/Serializable type")
        self.container_type = container_type
        self.element_type = element_type

    def serialize(self, value: Sequence) -> bytes:
        n = len(value)
        if self.element_type in self.type_mapping:
            fmt = "{}L{}{}".format(BYTES_ORDER, n, self.type_mapping[self.element_type])
            return struct.pack(fmt, n, *value)
        else:
            serializer = get_serializer(self.element_type)
            data = [serializer.serialize(item) for item in value]
            data.insert(0, struct.pack("{}L".format(BYTES_ORDER), n))
            return b"".join(data)

    def deserialize(self, buffer: bytes) -> Sequence:
        fmt = "{}L".format(BYTES_ORDER)
        n = struct.unpack(fmt, buffer[:struct.calcsize(fmt)])[0]
        buffer = buffer[struct.calcsize(fmt):]
        if self.element_type in self.type_mapping:
            fmt = "{}{}{}".format(BYTES_ORDER, n, self.type_mapping[self.element_type])
            data = self.container_type(struct.unpack(fmt, buffer[:struct.calcsize(fmt)]))
            buffer = buffer[struct.calcsize(fmt):]
            return data, buffer
        else:
            serializer = get_serializer(self.element_type)
            data = []
            for _ in range(n):
                value, buffer = serializer.deserialize(buffer)
                data.append(value)
            data = self.container_type(data)
            return data, buffer


class CustomSerializer(Serializer):
    def __init__(self, objtype):
        self.type_ = objtype

    def serialize(self, value) -> bytes:
        data = []
        for key, serializer in self.type_.mappings:
            v = getattr(value, key)
            data.append(serializer.serialize(v))
        return b"".join(data)

    def deserialize(self, buffer: bytes):
        data = {}
        for key, serializer in self.type_.mappings:
            value, buffer = serializer.deserialize(buffer)
            data[key] = value
        item = self.type_(**data)
        return item, buffer


class Serializable(metaclass=SerializableMeta):
    def serialize(self) -> bytes:
        return self.serializer.serialize(self)

    @classmethod
    def deserialize(cls, buffer: bytes):
        value, buffer = cls.serializer.deserialize(buffer)
        if len(buffer):
            warnings.warn(RuntimeWarning("buffer remain non-empty after deserializing"))
        return value

    def dump(self, filename):
        with open(filename, "wb") as f:
            f.write(self.serialize())

    @classmethod
    def load(cls, filename):
        with open(filename, "rb") as f:
            buf = f.read()
        return cls.deserialize(buf)


def get_serializer(objtype) -> Serializer:
    if issubclass(objtype, int):
        return BasicSerializer("L")
    elif issubclass(objtype, float):
        return BasicSerializer("d")
    elif issubclass(objtype, bytes):
        return BytesSerializer()
    elif issubclass(objtype, Sequence):
        element_type = objtype.__args__[0]
        container_type = objtype.__orig_bases__[0]
        return SequenceSerializer(container_type, element_type)
    elif issubclass(objtype, Serializable):
        return CustomSerializer(objtype)

import hashlib
import struct
import warnings
from .serialize import Serializable, Serializer, BYTES_ORDER


class Hashable(Serializable):
    def __init__(self):
        self._hash = None

    @property
    def hash(self):
        if not hasattr(self, "_hash") or self._hash is None:
            series = super(Hashable, self).serialize()
            self._hash = hashlib.sha256(series).digest()
        return self._hash

    def serialize(self):
        series = super(Hashable, self).serialize()
        return b"".join([series, self.hash])

    @classmethod
    def deserialize(cls, buffer):
        value, buffer = cls.serializer.deserialize(buffer)
        hash, buffer = buffer[:32], buffer[32:]
        if not value.hash == hash:
            raise ValueError("Hash unmatch")
        if len(buffer):
            warnings.warn(RuntimeWarning("buffer remain non-empty after deserializing"))
        return value

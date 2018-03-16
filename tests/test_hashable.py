import unittest
import hashlib
from snowcoin.blockchain.interface.hashable import Hashable
from snowcoin.blockchain.interface.serialize import SerializableAttribute


class HashableTestCast(unittest.TestCase):
    def setUp(self):
        class A(Hashable):
            a = SerializableAttribute('a', int)
        self.A = A
        self.a = A(a=1)

    def test_recover(self):
        hash_a = self.a.hash
        buf = self.a.serialize()
        b = self.A.deserialize(buf)
        hash_b = b.hash
        self.assertEqual(hash_a, hash_b)

    def hash_match(self):
        hash_a = self.a.hash
        buf = self.a.serialize()
        data, hash = buf[:-32], buf[-32:]
        self.assertEqual(hash, hash_a)
        encrypter = hashlib.sha256()
        encrypter.update(data)
        hash_b = encrypter.digest()
        self.assertEqual(hash, hash_b)


if __name__ == '__main__':
    unittest.main()
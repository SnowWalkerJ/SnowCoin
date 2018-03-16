import unittest
from snowcoin.blockchain.interface.serialize import *


class SerializerTestCast(unittest.TestCase):
    def setUp(self):
        class A(Serializable):
            a = SerializableAttribute("a", int)
            b = SerializableAttribute("b", float)

        class B(Serializable):
            m = SerializableAttribute("m", List[A])

        self.A = A
        self.B = B

    def test_int(self):
        a = 10
        serialier = get_serializer(int)
        buff = serialier.serialize(a)
        b, new_buff = serialier.deserialize(buff)
        self.assertEqual(len(new_buff), 0)
        self.assertEqual(b, 10)

    def test_float(self):
        a = 10.0
        serialier = get_serializer(float)
        buff = serialier.serialize(a)
        b, new_buff = serialier.deserialize(buff)
        self.assertEqual(len(new_buff), 0)
        self.assertAlmostEqual(b, 10.0)

    def test_list_float(self):
        a = [1.0, 3.1]
        serialier = get_serializer(List[float])
        buff = serialier.serialize(a)
        b, new_buff = serialier.deserialize(buff)
        self.assertEqual(len(new_buff), 0)
        self.assertListEqual(a, b)

    def test_list_int(self):
        a = [1, 2, 3]
        serialier = get_serializer(List[int])
        buff = serialier.serialize(a)
        b, new_buff = serialier.deserialize(buff)
        self.assertEqual(len(new_buff), 0)
        self.assertListEqual(a, b)

    def test_empty_list(self):
        a = []
        serializer = get_serializer(List[int])
        buff = serializer.serialize(a)
        b, new_buff = serializer.deserialize(buff)
        self.assertEqual(len(new_buff), 0)
        self.assertTrue(not b)

    def test_bytes(self):
        a = b"123!@#$ASgsa"
        serializer = get_serializer(bytes)
        buff = serializer.serialize(a)
        b, new_buff = serializer.deserialize(buff)
        self.assertEqual(len(new_buff), 0)
        self.assertEqual(a, b)

    def test_object(self):
        obj = self.B(m=[self.A(a=1, b=1.2)])
        buf = obj.serialize()
        obj_duplicate = self.B.deserialize(buf)
        self.assertEqual(obj_duplicate.m[0].a, 1)
        self.assertAlmostEqual(obj_duplicate.m[0].b, 1.2)


if __name__ == '__main__':
    unittest.main()
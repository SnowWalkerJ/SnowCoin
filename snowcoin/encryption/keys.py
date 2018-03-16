from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256, RIPEMD160
from base64 import b64encode
from typing import List


def key2address(public_key):
    x = SHA256.new(public_key).digest()
    x = RIPEMD160.new(x).digest()
    p = SHA256.new(x).digest()
    p = SHA256.new(p).digest()[:4]
    x = b"".join([x, p])
    return b64encode(x).encode()


class KeyPair:
    def __init__(self, private_key, passphrase=None):
        self._key = RSA.importKey(private_key, passphrase)
        self._public_key = self._key.publickey().exportKey('DER')
        self._address = key2address(self.public_key)

    def private_key(self, passphrase=None):
        return self._key.exportKey('DER', passphrase=passphrase)

    @property
    def public_key(self):
        return self._public_key

    @property
    def address(self):
        return self._address

    @classmethod
    def new(cls):
        key = RSA.generate(2048)
        return cls(key)
    

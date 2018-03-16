from Crypto.Signature import PKCS1_PSS
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA


def sign(msg, private_key):
    key = RSA.importKey(private_key)
    h = SHA.new(msg)
    signer = PKCS1_PSS.new(key)
    signature = signer.sign(h)
    return signature


def verify(msg, signature, public_key):
    key = RSA.importKey(public_key)
    h = SHA.new(msg)
    verifier = PKCS1_PSS.new(key)
    return verifier.verify(h, signature)

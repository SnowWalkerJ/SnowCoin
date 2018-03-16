from collections import namedtuple
from typing import List
import json
import hashlib
import Crypto
from ..encryption.signature import verify
from ..encryption.keys import key2address
from ..common.interface import Hashable, SerializableAttribute


class TransactionIn(Hashable):
    __slots__ = ['_block_hash', '_transaction_hash', '_n', '_public_key', '_signature', '_chain', '_transaction']
    block_hash = SerializableAttribute("block_hash", bytes)
    transaction_hash = SerializableAttribute("transaction_hash", bytes)
    n = SerializableAttribute("n", int)
    public_key = SerializableAttribute("public_key", bytes)
    signature = SerializableAttribute("signature", bytes)
    def __init__(self):
        self._chain = None
        self._transaction = None

    def _verify_is_owned(self) -> bool:
        key_valid = key2address(self.public_key) == self._transaction.trx_out[self.n].address
        signature_valid = verify(self.transaction_hash, self.signature, self.public_key)
        return key_valid and signature_valid

    def _verify_exists(self) -> bool:
        return self._transaction

    def bind(self, blockchain) -> bool:
        if self._chain == blockchain:
            return True
        try:
            block = blockchain[self.block_hash]
            transaction = block[self.transaction_hash]
        except KeyError:
            return False
        else:
            self._chain = blockchain
            self._block = block
            self._transaction = transaction
            return True

    def is_valid(self) -> bool:
        return self._verify_exists() and self._verify_is_owned() and not self._chain.is_cash_spent(self)

    @property
    def transaction(self):
        if self._transaction is None:
            raise RuntimeError("You need to bind this TransactionIn with a blockchain first.")
        return self._transaction

    @property
    def amount(self):
        if self._transaction is None:
            raise RuntimeError("You need to bind this TransactionIn with a blockchain first.")
        return self._transaction.data[self.n].amount


class TransactionOut(Hashable):
    __slots__ = ['_address', '_amount']
    address = SerializableAttribute("address", bytes)
    amount = SerializableAttribute("amount", float)

    def add_amount(self, value):
        self._amount += value
        self._hash = None


class Transaction(Hashable):
    __slots__ = ['_trx_in', '_trx_out', '_chain']
    trx_in = SerializableAttribute('trx_in', List[TransactionIn])
    trx_out = SerializableAttribute('trx_out', List[TransactionOut])
    def __init__(self):
        self._chain = None

    def bind(self, blockchain):
        self._chain = blockchain

    def is_valid(self) -> bool:
        """
        Check if a transaction is validate
        1. Sum of ins >= sum of outs
        2. Every in exists in the former blocks(six before)
        3. None of the ins has been spent
        4. The sender owns all the ins
        """
        
        for trx_in in self.trx_in:
            if not (trx_in.bind(self._chain) and trx_in.is_valid()):
                return False
        
        return self.fee >= 0

    @staticmethod
    def _verify_not_spent(trx_in: TransactionIn, blockchain) -> bool:
        endpoint = trx_in.block_hash
        block_hash = blockchain.head
        while True:
            block = blockchain.blocks[block_hash]
            for transaction in block.data.values():
                if trx_in in transaction.trx_in:
                    return False
            block_hash = block.parent
            if block_hash is None or block_hash == endpoint:
                break
        return True

    @property
    def total_in(self) -> float:
        return sum(trx_in.bind(self._chain) and trx_in.amount for trx_in in self.trx_in)
        
    @property
    def total_out(self) -> float:
        return sum(trx_out.amount for trx_out in self.trx_out)

    @property
    def fee(self) -> float:
        return self.total_out - self.total_in


class CoinBase(Transaction):
    def __init__(self, address):
        self.trx_in = []
        self.trx_out = [TransactionOut(address=address, amount=10.0)]

    def add_fee(self, fee):
        self.trx_out[0].amount += fee


import os
import pickle
import datetime
import json
import struct
from typing import List
from .transaction import Transaction
from ..common.interface import Hashable, SerializableAttribute


GENSIS_HASH = b'\x8d\x9d#K<!\x9b\x02t\xea\xdaC\x19.\x14_\x90\x9aA:n+\x04zR\x95o;5I\xad\xac'


class Block(Hashable):
    __slots__ = ['_parent', '_nounce', '_timestamp', '_data', '_chain', '_mapping']
    parent = SerializableAttribute("parent", bytes)
    nounce = SerializableAttribute('nounce', int)
    timestamp = SerializableAttribute("timestamp", int)
    data = SerializableAttribute("data", List[Transaction])
    def __init__(self):
        self._chain = None
        self._mapping = {i: trx.hash for i, trx in enumerate(self.data)}

    def bind(self, chain):
        self._chain = chain

    def is_valid(self) -> bool:
        coinbase_valid = self.data[0].total_out + sum(trx.fee for trx in self.data[1:]) < 10
        parent_valid = self.parent == self._chain.head
        transaction_valid = all(transaction.is_valid() for transaction in self.data[1:])
        gensis_valid = self.hash == GENSIS_HASH
        time_valid = True
        mission_complete = struct.unpack("<L", self.hash)[0] < self._chain.current_hardness
        return (parent_valid and transaction_valid and mission_complete and time_valid and coinbase_valid) or gensis_valid
        
    def __getitem__(self, transaction_hash):
        i = self._mapping[transaction_hash]
        return self.data[i]

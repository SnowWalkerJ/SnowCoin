from itertools import chain
from typing import Iterable, Union
import struct
from .block import Block
from ..db.redis_ import get_redis
from ..common.interface.serialize import Serializable, SerializableAttribute
from ..encryption.signature import verify


class OpenTransaction(Serializable):
    block_hash = SerializableAttribute('block_hash', bytes)
    transaction_hash = SerializableAttribute('transaction_hash', bytes)
    n = SerializableAttribute('n', int)


class BlockChain:
    def __init__(self):
        self._redis = get_redis()
        self._hardness = None
        
    def initialize(self):
        keys = self._redis.keys()
        if keys:
            self._redis.delete(*keys)
        gensis = Block(parent=b"0"*32, nounce=0, timestamp=0, data=[])
        self.append(gensis)

    @property
    def head(self) -> bytes:
        return self._redis.lindex("hashes", -1)

    @property
    def current_hardness(self) -> int:
        if self._hardness is None:
            hashes = self._redis.lrange("hashes", -1000, -1)
            timestamps = sorted([self[h].timestamp for h in hashes])
            average_time = (timestamps[-1] - timestamps[0]) / (len(timestamps) - 1)
            target_time = 600
            average_hardness = sum(struct.unpack("<L", h)[0] for h in hashes) / len(hashes)
            self._hardness = int(average_hardness * average_time / target_time)
        return self._hardness

    @property
    def open_transactions(self):
        return (OpenTransaction.deserialize(ot) for ot in self._redis.smembers('open_transactions'))

    def untrusted_blocks(self) -> Iterable[str]:
        """
        Hash of the latest six blocks.
        """
        return self._redis.lrange('hashes', -6, -1)

    def get_verified_blocks(self):
        return self._redis.lrange('hashes', 0, -7)

    def transactions(self):
        data = (self[k].data for k in self.list_blocks())
        return chain.from_iterable(data)

    def list_blocks(self):
        return self._redis.lrange('hashes', 0, -1)

    def is_cash_spent(self, transaction_in):
        raise NotImplementedError

    def __len__(self):
        return len(self._redis.keys("BLOCK:*"))

    def __getitem__(self, index: Union[bytes, int]) -> Block:
        if isinstance(index, int):
            index = self._redis.lindex("hashes", index)
        key = "BLOCK:{}".format(index)
        return Block.deserialize(self._redis.get(key))

    def append(self, block: Block):
        # Blocks
        block.bind(self)
        if not block.is_valid():
            raise RuntimeError("Block invalid")
        serial = block.serialize()
        self._redis.set("BLOCK:{}".format(block.hash), serial)
        self._redis.rpush("hashes", block.hash)
        self._redis.bgsave()
        self._hardness = None

        # Open transactions
        block_hash = block.hash
        open_transactions = []
        close_transactions = []
        for transaction in block.data:
            for transaction_in in transaction.trx_in:
                _block_hash = transaction_in.block_hash
                _transaction_hash = transaction_in.transaction_hash
                _n = transaction_in.n
                close_transactions.append(OpenTransaction(block_hash=_block_hash, transaction_hash=_transaction_hash, n=_n).serialize())
            for n in range(len(transaction.trx_out)):
                open_transactions.append(OpenTransaction(block_hash=block_hash, transaction_hash=transaction.hash, n=n).serialize())
        if close_transactions:
            self._redis.srem("open_transactions", *close_transactions)
        if open_transactions:
            self._redis.sadd("open_transactions", *open_transactions)

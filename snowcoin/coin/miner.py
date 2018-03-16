import numpy as np
import multiprocessing as mp
from datetime import datetime
from .wallet import Wallet
from ..common.settings import CONFIG
from ..blockchain import Block, Transaction, CoinBase


nounce_uplimit = int("F"*8, 16)
block_size = 1000


class TemperalBlock(Block):
    def __init__(self, address):
        self.data.append(Coinbase(address))

    def update_nounce(self, nounce):
        self._nounce = nounce
        self._hash = None

    def update_timestamp(self):
        self._timestamp = datetime.now().timestamp()
        self._hash = None

    def update_parent(self, parent):
        self._parent = parent
        self._hash = None

    def insert_transaction(self, transaction: Transaction):
        transaction.bind(self._chain)
        self.data[0].trx_out.add_fee(transaction.fee)
        self.data.append(transaction)
        self._hash = None


class Miner(mp.Process):
    def __init__(self, wallet: Wallet, queue):
        self.wallet = wallet
        self.queue = queue
        self.transactions_cache = []
        self.block = TemperalBlock(
            address=CONFIG['miner']['address'],
            parent=self.wallet.head,
            nounce=0,
            timestamp=int(datetime.now().timestamp()),
            data=[],
        )

    def run(self):
        for nounce in np.random.randint(0, nounce_uplimit, block_size):
            self.block.update_nounce(nounce)
            if self.block.hash < self.wallet.current_hardness:
                return True
        self.block.update_timestamp()
        self.block.update_parent(self.wallet.blockchain.head)

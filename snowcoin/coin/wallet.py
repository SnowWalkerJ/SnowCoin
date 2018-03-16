import Pyro4
from ..encryption.keys import KeyPair
from ..blockchain import BlockChain, Block


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Wallet(BlockChain):
    def __init__(self, keys: KeyPair):
        self.keys = keys
        self._money = None
        super(Wallet, self).__init__()

    @property
    def address(self):
        return self.keys.address

    @property
    def money(self):
        if self._money is None:
            money = []
            for ot in self.open_transactions:
                trx_out = self[ot.block_hash][ot.transaction_hash].trx_out[ot.n]
                if trx_out.address == self.address:
                    money.append(ot)
            self._money = money
        return self._money

    def amount(self) -> float:
        amount = 0.0
        for ot in self.money:
            amount += self[ot.block_hash][ot.transaction_hash].trx_out[ot.n].amount
        return amount


if __name__ == '__main__':
    Pyro4.Daemon.serveSimple({
        Wallet: 'snowcoin.wallet',
    })

import struct
import gevent
import signal
from gevent.event import Event

from vanilla.abci.server import ABCIServer
from vanilla.utils import from_hex, big_endian_to_int
from vanilla.abci.types_pb2 import ResponseInfo, BadNonce
from vanilla.abci.application import BaseApplication, Result

"""
Counter example
Try it out:
1. Start this app (python counter_example.py)
2. Start a Tendermint node (tendermint node)
3. Send Txs (curl -s http://localhost...)
"""
class SimpleCounter(BaseApplication):
    def __init__(self):
        self.hashCount = 0
        self.txCount = 0
        self.serial = False

    def info(self):
        print('ran info')
        r = ResponseInfo()
        r.data = '# hashes: {} # txs: {}'.format(self.hashCount, self.txCount)
        r.version = '2.0'
        return r

    def set_option(self, key, value):
        if key == "serial" and value == "on":
            self.serial = True
        return ""

    def deliver_tx(self, tx):
        print('deliver_tx')
        if self.serial:
            txByteArray = bytearray(tx)
            if len(tx) >= 2 and tx[:2] == "0x":
                txByteArray = from_hex(tx)
            txValue = big_endian_to_int(txByteArray)
            if txValue != self.txCount:
                return Result.error(code=BadNonce, log='bad nonce')
        self.txCount += 1
        return Result.ok()

    def check_tx(self, tx):
        if self.serial:
            txByteArray = bytearray(tx)
            if len(tx) >= 2 and tx[:2] == "0x":
                txByteArray = from_hex(tx)
            txValue = big_endian_to_int(txByteArray)
            print(txValue)
            if txValue != self.txCount:
                return Result.error(code=BadNonce, log='bad nonce')
        return Result.ok(log='thumbs up')

    def begin_block(self, hashv, header):
        print('begin block')
        print("last block: {}".format(header.height))

    def commit(self):
        print('commit')
        self.hashCount += 1
        if self.txCount == 0:
            return Result.ok(data='')
        h = struct.pack('>Q', self.txCount)
        return Result.ok(data=h)

if __name__ == '__main__':
    app = ABCIServer(app=SimpleCounter())
    app.start()

    # wait for interrupt
    evt = Event()
    gevent.signal(signal.SIGQUIT, evt.set)
    gevent.signal(signal.SIGTERM, evt.set)
    gevent.signal(signal.SIGINT, evt.set)
    evt.wait()

    app.stop()

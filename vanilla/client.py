import json
import requests
import itertools
import base64

from .utils import str_to_bytes, obj_to_str, bytes_to_str, is_string, to_hex, is_bytes

AGENT='vanilla.blockchain/0.1'

class RpcClient(object):
    """Tendermint RPC client: json-rpc requests over HTTP
    """
    def __init__(self, host="127.0.0.1", port=46657):
        # Tendermint endpoint
        self.uri = "http://{}:{}".format(host, port)

        # Keep a session
        self.session = requests.Session()

        # Request counter for json-rpc
        self.request_counter = itertools.count()

        # request headers
        self.headers = {
            'user-agent': AGENT,
            'Content-Type': 'application/json'
        }

    def call(self, method, params):
        value = str(next(self.request_counter))
        encoded = json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": value,
        })

        r = self.session.post(
            self.uri,
            data=encoded,
            headers=self.headers,
            timeout=3
        )

        #try:
        #    r.raise_for_status()
        #except Exception as er:
        #    print(er)

        response = r.content


        if is_string(response):
            response = json.loads(bytes_to_str(response))

        if response["error"]:
            raise ValueError(response["error"])
        return response['result']

    @property
    def is_connected(self):
        try:
            response = self.status()
        except IOError:
            return False
        else:
            assert(response['node_info'])
            return True
        assert False

    def status(self):
        return self.call('status', [])

    def info(self):
        return self.call('abci_info', [])

    def genesis(self):
        return self.call('genesis', [])

    def unconfirmed_txs(self):
        return self.call('unconfirmed_txs', [])

    def validators(self):
        return self.call('validators', [])

    def get_block(self, height='latest'):
        if height == 'latest' or not height:
            v = self.status()['latest_block_height']
            return self.call('block', [v])
        if height <= 0:
            raise ValueError("Height must be greater then 0")
        return self.call('block', [height])

    def get_block_range(self, min=0, max=0):
        """ By default returns 20 blocks """
        return self.call('blockchain', [min, max])

    def get_commit(self, height=1):
        """ Get commit information for a given height """
        if height == 'latest' or not height:
            v = self.status()['latest_block_height']
            return self.call('commit', [v])
        if height <= 0:
            raise ValueError("Height must be greater then 0")
        return self.call('commit', [height])

    def query(self, path, data, proof=False):
        d = to_hex(data)
        return self.call('abci_query', [path, d[2:], proof])

    def _send_transaction(self, name, tx):
        if is_bytes(tx):
            tx = bytes_to_str(base64.b64encode(tx))
        return self.call(name, [tx])

    def send_tx_commit(self, tx):
        return self._send_transaction('broadcast_tx_commit', tx)

    def send_tx_sync(self, tx):
        return self._send_transaction('broadcast_tx_sync', tx)

    def send_tx_async(self, tx):
        return self._send_transaction('broadcast_tx_async', tx)

    def get_tx(self, h, proof=False):
        #txhash = base64.b64encode(str_to_bytes('0x'+h))
        #return self.call('tx', [txhash,proof])
        # this is a mess - trying to make this work!
        pass

import inspect
import logging, colorlog

import rlp
import json
import os.path

from abci import (
    ABCIServer,
    BaseApplication,
    ResponseInfo,
    ResponseQuery,
    Result
)
from abci.types_pb2 import OK, InternalError

from .keys import Key
from .transactions import Transaction
from .state import State, StateCache, Storage
from .utils import str_to_bytes, int_to_big_endian, is_hex, from_hex

def create_logger(app):
    logger = logging.getLogger('pytendermint.app')
    handler = logging.StreamHandler()

    logger.setLevel(logging.INFO)

    if app.debug:
        logger.setLevel(logging.DEBUG)

    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
		    'INFO':     'green',
		    'WARNING':  'yellow',
		    'ERROR':    'red',
		    'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def setup_app_state(root_dir):
    if not os.path.exists(root_dir):
        msg = "Cannot find tendermint directory {}".format(root_dir)
        raise FileNotFoundError(msg)

    tm_genesis = os.path.join(root_dir, 'genesis.json')
    if not os.path.exists(tm_genesis):
        msg = "Cannot find tendermint genesis file in {}".format(root_dir)
        raise FileNotFoundError(msg)

    genesis_chain_id = ''
    with open(tm_genesis) as gf:
        info = json.loads(gf.read())
        genesis_chain_id = info['chain_id']

    dbname = os.path.join(root_dir, "{}.vdb".format(genesis_chain_id))

    state, is_new  = State.load_state(dbname)

    state.chain_id = str_to_bytes(state.chain_id)
    genesis_chain_id = str_to_bytes(genesis_chain_id)

    if state.chain_id == genesis_chain_id:
        return (state, False)

    if not is_new and state.chain_id != genesis_chain_id:
        raise TypeError(
            "chain_id's don't match! Are you sure you're using the correct"
            " Tendermint directory?"
        )

    if is_new:
        state.chain_id = genesis_chain_id
        state.save()

    return (state, is_new)

class TendermintApp(BaseApplication):
    # Enable for testing.  Uses in-memory (temp) storage and doesn't
    # start the server. 'mock_test_state' is for assigning abitrary
    # state for testing without using storage
    mock_test_state = None

    # Current version
    version = "0.2"

    # Debug loglevel
    debug = True

    def __init__(self, homedir, port=46658):
        # This should match the basedir used by tendermint
        # Directory for storing application state db.
        # This must be the same as the Tendermint home dir
        self.rootdir = homedir

        # Port to run ABCI server
        self.port = port

        # This will execute the provided function (if any) the first time the
        # application is started. It's a good place to initiate any genesis
        # state you may want to include in the application. Once the statedb is
        # created for the app, this will be ignored
        self._on_init = None

        # Called to validate a transaction before including it the blockchain
        # memory pool for consideration.  If not provided a function, all
        # transactions will be accepted.  The function expects a single param 'ctx'
        # that includes the current tx and the access to application state cache
        #self._validate_tx = None

        # Handlers for actually processing a transaction and updating application
        # state. The maps a call string to a given function.
        self._tx_handlers = {}

        # Query handlers to process custom queries
        self._query_handlers = {}

        # State and caches
        self._storage = None

        # Logger
        self.log = create_logger(self)

        self.log.info("using tendermint dir: {}".format(self.rootdir))

    def __check_for_param(self,func, required_params):
        """ Checks that any provided application functions contain the required
        number of positional parameters. If they don't, it throws an Error
        """
        sig = inspect.signature(func)
        if len(sig.parameters.values()) < required_params:
            raise TypeError(
                "The {} function is missing the "
                "{} required param(s)".format(func.__name__, required_params)
            )

    ## DECORATORS ##
    def on_initialize(self):
        """ Called on the very first run of the application. Can be used to
        initialize genesis state
        """
        def decorator(f):
            self.__check_for_param(f,1)
            self._on_init = f
            return f
        return decorator

    def on_transaction(self, tx_call_name):
        """ A decorator for functions that implement core business logic and
        can alter application state.  The provided function MUST accept 2
        params 'tx' and 'db', and return True or False depending on the success
        or failure of the logic.
        The 'tx_call_name' must match the value set in Tx.call
        """
        if not tx_call_name:
            raise TypeError("Missing call name for the Tx handler")
        def decorator(f):
            self.__check_for_param(f,2)
            self._tx_handlers[str_to_bytes(tx_call_name)] = f
            return f
        return decorator

    def on_query(self, path):
        if not path:
            raise TypeError("Missing path name for the Query handler")
        def decorator(f):
            self.__check_for_param(f,2)
            self._query_handlers[str_to_bytes(path)] = f
            return f
        return decorator


    #           * ABCI specific callbacks below. *
    # This is the required ABCI interface for interacting with a
    # Tendermint node
    def __decode_incoming_tx(self, rawtx):
        self.log.debug("Raw tx: {}".format(rawtx))
        if is_hex(rawtx):
            rawtx = from_hex(rawtx)

        return Transaction.decode(rawtx)

    def set_option(self, req):
        return "not implemented in pytendermint - YAGNI"

    def init_chain(self, validators):
        self.log.debug("init_chain validators: {}".format(validators))
        # First run create state
        state, is_new = setup_app_state(self.rootdir)
        self._storage = Storage(state)
        if is_new and self._on_init:
            self._on_init(self._storage.confirmed)
            # Commit the data so it's available
            self._storage.state.save()

    def info(self, req):
        # Load state
        if not self._storage:
            state, _ = setup_app_state(self.rootdir)
            self._storage = Storage(state)

        result = ResponseInfo()
        result.last_block_height = self._storage.state.last_block_height
        result.last_block_app_hash = self._storage.state.last_block_hash
        result.data = "pyTendermint app v{}".format(self.version)
        result.version = self.version
        return result

    def check_tx(self, req):
        # Decode Tx
        decoded_tx = self.__decode_incoming_tx(req.check_tx.tx)

        # Get the account for the sender
        # We use unconfirmed cache to allow multiple Tx per block
        if not decoded_tx.sender:
            return Result.error(code=InternalError, log="No Sender - is the Tx signed?")

        acct = self._storage.unconfirmed.get_account(decoded_tx.sender)
        if not acct:
            return Result.error(code=InternalError, log="Account not found")

        # Check the nonce
        if acct.nonce != decoded_tx.nonce:
            return Result.error(code=InternalError, log="Bad nonce")

        # increment the account nonce
        self._storage.unconfirmed.increment_nonce(decoded_tx.sender)

        # verify the signature
        if not Key.verify(acct.pubkey, decoded_tx.signature):
            return Result.error(code=InternalError, log="Invalid Signature")

        # Check if this is a value transfer, if so make sure sender has an
        # acct balance > tx.value
        if decoded_tx.value > 0 and acct.balance < decoded_tx.value:
            return Result.error(code=InternalError, log="Insufficient balance for transfer")

        return Result.ok()

    def deliver_tx(self, req):
        tx = self.__decode_incoming_tx(req.deliver_tx.tx)
        if not tx.call in self._tx_handlers:
            return Result.error(code=InternalError, log="No matching Tx handler")

        if not self._tx_handlers[tx.call](tx, self._storage.confirmed):
            return Result.error(code=InternalError,log="Tx Handler returned false or None")

        return Result.ok()

    def query(self, req):
        path = str_to_bytes(req.query.path)
        key = req.query.data

        if not path:
            self.log.error("Missing path value")
            return ResponseQuery(code=InternalError, value=b'missing path value')
        if not key:
            self.log.error("Missing key value")
            return ResponseQuery(code=InternalError, value=b'missing key value')

        # Format ints to big_endianss
        def format_if_needed(value):
            if isinstance(value, int):
                return int_to_big_endian(value)
            else:
                return value

        # built in call for creating Txs
        if path == b'/tx_nonce':
            # Query account in the unconfirmed cache
            acct = self._storage.unconfirmed.get_account(key)
            return ResponseQuery(code=OK, value=format_if_needed(acct.nonce))

        # Try the handler(s)
        if path in self._query_handlers:
            bits = self._query_handlers[path](key, self._storage.confirmed)
            return ResponseQuery(code=OK, value=format_if_needed(bits))

        errmsg = "No handler found for {}".format(path)
        return ResponseQuery(code=InternalError, value=str_to_bytes(errmsg))

    def commit(self, req):
        apphash = self._storage.commit()
        return Result.ok(data=h)

    def begin_block(self, req):
        self._storage.state.last_block_height = req.begin_block.header.height

    def no_match(self, req):
        return to_response_exception("Unknown ABCI request!")

    def mock_run(self):
        """ For testing without the server
        """
        self.log.info("running in test mode")
        state, _  = State.load_state()
        self._storage = Storage(state)
        if self._on_init:
            self._on_init(self._storage.confirmed)
            self._storage.commit()

    def run(self):
        """ Run the app in the py-abci server
        """
        server = ABCIServer(app=self)
        server.run()

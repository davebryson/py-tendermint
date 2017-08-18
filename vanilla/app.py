import inspect
import logging, colorlog

import rlp
import json
#import crayons
import os.path

from .abci.wire import *
from .abci.messages import *
from .abci.types_pb2 import Request, ResponseEndBlock
from .abci.application import Result

from .transactions import Transaction
from .state import State, StateCache, Storage
from .utils import str_to_bytes, int_to_big_endian

from gevent.event import Event
from gevent.server import StreamServer

def create_logger(app):
    logger = logging.getLogger('vanilla.app')
    handler = logging.StreamHandler()

    if app.debug and logger.level == logging.NOTSET:
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
    log.debug("attempting to setup from tendermint dir: {}".format(root_dir))

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

    if state.chain_id == genesis_chain_id:
        log.debug('using existing chain: {}'.format(genesis_chain_id))
        return (state, False)

    if not is_new and state.chain_id != genesis_chain_id:
        raise TypeError(
            "chain_id's don't match! Are you sure you're using the correct"
            " Tendermint directory?"
        )

    if is_new:
        log.debug('first run with chainid: {}'.format(genesis_chain_id))
        state.chain_id = genesis_chain_id

    return (state, is_new)


class VanillaApp(object):

    # Enable for testing.  Uses in-memory (temp) storage and doesn't
    # start the server. 'mock_test_state' is for assigning abitrary
    # state for testing without using storage
    mock_test_state = None

    # Current version
    version = "0.1"

    # Debug loglevel
    debug = False


    def __init__(self, homedir, port=46658):

        # This should match the basedir used by tendermint
        #info_message("using tendermint dir at: {}".format(homedir))

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
        self._validate_tx = None

        # Handlers for actually processing a transaction and updating application
        # state. The maps a call string to a given function.
        self._process_tx_handlers = {}

        # Handlers that respond to querying the application state.
        self._query_handlers = {}

        # State and caches
        self._storage = None

        # Logger
        self.log = create_logger(self)

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

    def on_initialize(self):
        """ Called on the very first run of the application. Can be used to
        initialize genesis state
        """
        def decorator(f):
            self.__check_for_param(f,1)
            self._on_init = f
            return f
        return decorator

    def validate_transaction(self):
        """Single validator for the app.  This is based on the idea that the
        single Transaction can be handled by a single validator.  Used to 'check'
        transaction to see whether or not they should be included in the mempool
        or ignored.
        """
        def decorator(f):
            self.__check_for_param(f,2)
            self._validate_tx = f
            return f
        return decorator

    def process_transaction(self, rule):
        """ A decorator for functions that implement core business logic and
        can alter application state.  The provided function MUST accept a 2
        params 'tx' and 'storage'. The 'rule' must match the value set in Tx.call
        """
        if not rule:
            raise TypeError("Missing call name for the Tx handler")

        def decorator(f):
            self.__check_for_param(f,2)
            self._process_tx_handlers[str_to_bytes(rule)] = f
            return f
        return decorator

    def querystate(self, rule):
        """Handlers to query the state of the application.  User has access to
        both confirmed and unconfirmed cache via the storage class passed as a
        parameter to decorated functions.
        """
        def decorator(f):
            self.__check_for_param(f,2)
            self._query_handlers[str_to_bytes(rule)] = f
            return f
        return decorator

    def __handle_abci_call(self,req_type, req):
        """ Called from the server to handle ABCI requests
        """
        handler = getattr(self, req_type, self.no_match)
        return handler(req)

    #           * ABCI specific callbacks below. *
    # This is the required ABCI interface for interacting with a
    # Tendermint node
    def echo(self, req):
        return to_response_echo(req.echo.message)

    def flush(self, req):
        flush_resp = to_response_flush()
        return to_response_flush()

    def set_option(self, req):
        result = "not implemented in vanilla - YAGNI"
        return to_response_set_option(result)

    def info(self, req):
        result = ResponseInfo()
        result.last_block_height = self._storage.state.last_block_height
        result.last_block_app_hash = self._storage.state.last_block_hash
        r.data = "Vanilla app v{}".format(self.version)
        r.version = self.version
        return to_response_info(result)

    def check_tx(self, req):
        decoded_tx = Transaction.decode(req.check_tx.tx)
        result = Result.ok()

        if self._validate_tx:
            result = self._validate_tx(decoded_tx, self._storage)
            if not result:
                result = Result.error(
                    code=InternalError,
                    log="Validate tx function didn't return a result")

        return to_response_check_tx(result.code, result.data, result.log)

    def deliver_tx(self, req):
        tx = Transaction.decode(req.deliver_tx.tx)
        result = Result.error(code=InternalError, log="No matching Tx handler")

        if tx.call in self._process_tx_handlers:
            result = self._process_tx_handlers[tx.call](tx, self._storage)
            if not result:
                result = Result.error(
                    code=InternalError,
                    log="Transaction handler did not return a result")

        return to_response_deliver_tx(result.code, result.data, result.log)

    def query(self, req):
        key = str_to_bytes(req.query.path)
        searchvalue = req.query.data

        # default response
        resp = ResponseQuery(code=OK, value=b'')
        if key in self._query_handlers:
            result = self._query_handlers[key](searchvalue,self._storage)
            if result:
                resp.code = result.code
                # Can't send numbers in the value field, they must be bytes
                if isinstance(result.data, int):
                    result.value = int_to_big_endian(result.data)
                else:
                    resp.value = result.data
        return to_response_query(resp)

    def commit(self, req):
        apphash = self._storage.commit()
        return to_response_commit(OK, apphash, '')

    def begin_block(self, req):
        self._storage.state.last_block_height = req.begin_block.header.height
        #self.app.begin_block(req.begin_block.hash, req.begin_block.header)
        return to_response_begin_block()

    def end_block(self, req):
        #result = self.app.end_block(req.end_block.height)
        return to_response_end_block(ResponseEndBlock())

    def init_chain(self, validators):
        #self.app.init_chain(validators)
        return to_response_init_chain()

    def no_match(self, req):
        return to_response_exception("Unknown request!")

    # Server handler.  Receives message from tendermint and process accordingly
    def __handle_connection(self, socket, address):
        self.log.info('connection from: {}:{}'.format(address[0], address[1]))
        while True:
            inbound = socket.recv(1024)
            msg_length = len(inbound)
            data = BytesIO(inbound)
            if not data or msg_length == 0: return

            while data.tell() < msg_length:
                try:
                    req, data_read  = read_message(data, Request)
                    if data_read == 0: return

                    req_type = req.WhichOneof("value")
                    result = self.__handle_abci_call(req_type, req)
                    response = write_message(result)

                    socket.sendall(response)
                except Exception as e:
                    self.log.error(e)

        socket.close()

    def mock_run(self):
        """ For testing without the abci server
        """
        self.log.info("running in test mode")
        state, _  = State.load_state('')
        self._storage = Storage(state)
        if self._on_init:
            self._on_init(self._storage)

    def run(self):
        """ Run the app in an ABCI enabled server
        """
        state, is_new = setup_app_state(self.rootdir)
        self._storage = Storage(state)
        if is_new and self._on_init:
            self._on_init(self._storage)

        self.server = StreamServer(('0.0.0.0', port), handle=self.__handle_connection)
        self.server.start()
        self.log.info('VanillaApp started on port: {}'.format(self.port))

        evt = Event()
        gevent.signal(signal.SIGQUIT, evt.set)
        gevent.signal(signal.SIGTERM, evt.set)
        gevent.signal(signal.SIGINT, evt.set)
        evt.wait()

        self.log.info("shutting down the application")

        self.server.stop()

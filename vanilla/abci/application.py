from .messages import *
from ..utils import str_to_bytes
from .types_pb2 import *

class Result(object):
    def __init__(self, code=OK, data=b'', log=''):
        self.code = code
        self.data = str_to_bytes(data)
        self.log = log

    @classmethod
    def ok(cls, data=b'', log=''):
        data = str_to_bytes(data)
        return cls(OK, data, log)

    @classmethod
    def error(cls, code=InternalError, data=b'',log=''):
        data = str_to_bytes(data)
        return cls(code, data, log)

    def is_ok(self):
        return self.code == OK

    def str(self):
        return "ABCI[code:{}, data:{}, log:{}]".format(self.code, self.data, self.log)

class BaseApplication(object):
    """
    Base App extends this and override what's needed for your app
    """
    def info(self):
        r = ResponseInfo()
        r.data = "default"
        return r

    def set_option(self, k, v):
        return 'key: {} value: {}'.format(k,v)

    def deliver_tx(self, tx):
        return Result.ok(data='delivertx')

    def check_tx(self, tx):
        return Result.ok(data='checktx')

    def query(self, reqQuery):
        rq = ResponseQuery(code=OK, key=reqQuery.data, value=b'example result')
        return rq

    def commit(self):
        return Result.ok(data='commit #')

    def init_chain(self, validators):
        pass

    def begin_block(self, hash, header):
        pass

    def end_block(self, height):
        return ResponseEndBlock()

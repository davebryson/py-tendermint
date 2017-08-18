from .wire import *
from .messages import *
from .application import BaseApplication
from .types_pb2 import Request

from gevent.server import StreamServer

class ProtocolHandler(object):

    def __init__(self, app):
        self.app = app

    def process(self,req_type, req):
        handler = getattr(self, req_type, self.no_match)
        return handler(req)

    def echo(self, req):
        return write_message(to_response_echo(req.echo.message))

    def flush(self, req):
        flush_resp = to_response_flush()
        return write_message(to_response_flush())

    def info(self, req):
        result = self.app.info()
        response = to_response_info(result)
        return write_message(response)

    def set_option(self, req):
        result = self.app.set_option(req.set_option.key,req.set_option.value)
        response = to_response_set_option(result)
        return write_message(response)

    def check_tx(self, req):
        result = self.app.check_tx(req.check_tx.tx)
        response = to_response_check_tx(result.code, result.data, result.log)
        return write_message(response)

    def deliver_tx(self, req):
        result = self.app.deliver_tx(req.deliver_tx.tx)
        response = to_response_deliver_tx(result.code, result.data, result.log)
        return write_message(response)

    def query(self, req):
        result = self.app.query(req.query)
        response = to_response_query(result)
        return write_message(response)

    def commit(self, req):
        result = self.app.commit()
        response = to_response_commit(result.code, result.data, result.log)
        return write_message(response)

    def begin_block(self, req):
        self.app.begin_block(req.begin_block.hash, req.begin_block.header)
        return write_message(to_response_begin_block())

    def end_block(self, req):
        result = self.app.end_block(req.end_block.height)
        return write_message(to_response_end_block(result))

    def init_chain(self, validators):
        self.app.init_chain(validators)
        return write_message(to_response_init_chain())

    def no_match(self, req):
        response = to_response_exception("Unknown request!")
        return write_message(response)


class ABCIServer(object):

    def __init__(self, port=46658, app=None):
        if not app or not isinstance(app, BaseApplication):
            raise Exception(crayons.red("Application missing or not an instance of Base Application"))
        self.port = port
        self.protocol = ProtocolHandler(app)
        self.server = StreamServer(('0.0.0.0', port), handle=self.__handle_connection)

    def start(self):
        self.server.start()
        print(" ABCIServer started on port: {}".format(self.port))

    def stop(self):
        self.server.stop()

    def __handle_connection(self, socket, address):
        print(' ... connection from: {}:{} ...'.format(address[0], address[1]))
        while True:
            inbound = socket.recv(1024)
            msg_length = len(inbound)
            data = BytesIO(inbound)
            if not data or msg_length == 0: return

            while data.tell() < msg_length:
                try:
                    req, err  = read_message(data, Request)
                    # TODO: an err should be 1 ...
                    if err == 0: return

                    req_type = req.WhichOneof("value")

                    response = self.protocol.process(req_type, req)
                    socket.sendall(response)
                except Exception as e:
                    print(e)

        socket.close()

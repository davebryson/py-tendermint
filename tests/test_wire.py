from io import BytesIO

from vanilla.abci.wire import *
from vanilla.abci.messages import *
from vanilla.abci.server import ProtocolHandler
from vanilla.abci.types_pb2 import Request

def test_varints():
    buffer = BytesIO()
    write_varint(30, buffer)
    r = [x for x in buffer.getvalue()]
    assert r == [1, 30]
    assert 30 == read_varint(BytesIO(buffer.getvalue()))

    buffer = BytesIO()
    write_varint(1001, buffer)
    r = [x for x in buffer.getvalue()]
    assert r == [2, 3, 233]
    assert 1001 == read_varint(BytesIO(buffer.getvalue()))

def test_encoding_decoding():
    #b'\x01\x02\x1a\x00'  request.info with length
    #b'\x1a\x00' info w/o length
    echo = to_request_echo('hello')
    raw = write_message(echo)
    buffer = BytesIO(raw)
    req, _ = read_message(buffer, Request)
    assert 'echo' == req.WhichOneof("value")

    info = to_request_info()
    raw1 = write_message(info)
    buffer1 = BytesIO(raw1)
    req1, _ = read_message(buffer1, Request)
    assert 'info' == req1.WhichOneof("value")

def test_flow():
    from io import BytesIO
    # info + flush
    inbound = b'\x01\x02\x1a\x00\x01\x02\x12\x00'
    data = BytesIO(inbound)

    req_type,_  = read_message(data, Request)
    assert 'info' == req_type.WhichOneof("value")

    req_type2, _  = read_message(data, Request)
    assert 'flush' == req_type2.WhichOneof("value")

    assert data.read() == b''
    data.close()

    data2 = BytesIO(b'')
    req_type, fail  = read_message(data2, Request)
    assert fail == 0
    assert req_type == None

    data3 = BytesIO(b'\x01')
    req_type, fail  = read_message(data3, Request)
    assert fail == 0

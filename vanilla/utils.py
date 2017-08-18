import os
import os.path
from pathlib import Path

from math import ceil
from sha3 import keccak_256
from rlp.utils import decode_hex, encode_hex

def home_dir(*paths):
    """
    Create a path to dirs/file in OS home dir
    Ex: home_dir('temp', 'ex.txt') is:
    ~/temp/ex.txt
    """
    home = str(Path.home())
    return os.path.join(home,*paths)

def make_db_name(base, chainid):
    return home_dir(base, "{}.vdb".format(chainid))


def int_to_big_endian(value):
    byte_length = max(ceil(value.bit_length() / 8), 1)
    return (value).to_bytes(byte_length, byteorder='big')

def big_endian_to_int(value):
    return int.from_bytes(value, byteorder='big')

def str_to_bytes(data):
    if isinstance(data, str):
        return data.encode('utf-8')
    return data

def bytes_to_str(value):
    if isinstance(value, str):
        return value
    return value.decode('utf-8')

def remove_0x_head(s):
    return s[2:] if s[:2] in (b'0x', '0x') else s

def is_hex(s):
    return (isinstance(s, str) and s[:2] == '0x')

def to_hex(value):
    return '0x' + encode_hex(value)

def from_hex(value):
    v = remove_0x_head(value)
    return decode_hex(v)

def keccak(value):
    value = str_to_bytes(value)
    return keccak_256(value).digest()

assert keccak(b'') == b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p", "Incorrect sha3.  Make sure it's keccak"  # noqa: E501

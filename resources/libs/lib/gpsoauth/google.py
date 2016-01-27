import base64
import hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from .util import bytes_to_long, long_to_bytes


def key_from_b64(b64_key):
    binaryKey = base64.b64decode(b64_key)

    i = bytes_to_long(binaryKey[:4])
    mod = bytes_to_long(binaryKey[4:4+i])

    j = bytes_to_long(binaryKey[i+4:i+4+4])
    exponent = bytes_to_long(binaryKey[i+8:i+8+j])

    key = RSA.construct((mod, exponent))

    return key


def key_to_struct(key):
    mod = long_to_bytes(key.n)
    exponent = long_to_bytes(key.e)

    return '\x00\x00\x00\x80' + mod + '\x00\x00\x00\x03' + exponent


def parse_auth_response(text):
    response_data = {}
    for line in text.split('\n'):
        if not line:
            continue

        key, _, val = line.partition('=')
        response_data[key] = val

    return response_data


def signature(email, password, key):
    signature = []
    signature.append('\x00')

    struct = key_to_struct(key)
    signature.extend(hashlib.sha1(struct).digest()[:4])

    cipher = PKCS1_OAEP.new(key)
    encrypted_login = cipher.encrypt((email + u'\x00' + password).encode('utf-8'))

    signature.extend(encrypted_login)

    return base64.urlsafe_b64encode(''.join(signature))

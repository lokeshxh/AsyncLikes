import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from app.protobuf_handler import create_uid_protobuf


def encrypt_message(plaintext):
    try:
        key = b"Yg&tc%DEuh6%Zc^8"
        iv = b"6oyZDr22E3ychjM%"
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext, AES.block_size)
        encrypted_message = cipher.encrypt(padded_message)
        return binascii.hexlify(encrypted_message).decode("utf-8")
    except Exception:
        return None


def enc(uid):
    protobuf_data = create_uid_protobuf(uid)
    if protobuf_data is None:
        return None
    return encrypt_message(protobuf_data)

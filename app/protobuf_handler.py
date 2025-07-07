from proto import like_pb2, like_count_pb2, uid_generator_pb2
from google.protobuf.message import DecodeError


def create_like_protobuf(user_id, region):
    try:
        message = like_pb2.like()
        message.uid = int(user_id)
        message.region = region
        return message.SerializeToString()
    except Exception:
        return None


def create_uid_protobuf(uid):
    try:
        message = uid_generator_pb2.uid_generator()
        message.lokesh_ = int(uid)
        message.garena = 1
        return message.SerializeToString()
    except Exception:
        return None


def decode_protobuf(binary):
    try:
        items = like_count_pb2.Info()
        items.ParseFromString(binary)
        return items
    except DecodeError:
        return None
    except Exception:
        return None

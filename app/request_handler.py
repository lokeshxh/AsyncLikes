import aiohttp
import asyncio
import requests
from app.encryption import encrypt_message
from app.protobuf_handler import create_like_protobuf, decode_protobuf


async def send_request(encrypted_uid, token, url):
    try:
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB49",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=edata, headers=headers) as response:
                return await response.text()
    except Exception:
        return None


async def send_multiple_requests(uid, server_name, url, tokens):
    region = server_name
    protobuf_message = create_like_protobuf(uid, region)
    if protobuf_message is None:
        return None
    encrypted_uid = encrypt_message(protobuf_message)
    if encrypted_uid is None:
        return None

    tasks = []
    for token_doc in tokens:
        token = token_doc["token"]
        tasks.append(send_request(encrypted_uid, token, url))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results


def make_request(encrypt, server_name, token):
    if server_name == "IND":
        url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name in {"NX", "US"}:
        url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

    edata = bytes.fromhex(encrypt)
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB49",
    }
    try:
        response = requests.post(url, data=edata, headers=headers, verify=False)
        return decode_protobuf(response.content)
    except Exception:
        return None
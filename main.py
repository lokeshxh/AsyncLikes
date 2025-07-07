from flask import Flask, request, jsonify, Response
import asyncio
import json
from pymongo import MongoClient
from google.protobuf.json_format import MessageToJson
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests
import secrets

# Flask app init
app = Flask(__name__)

# MongoDB init
client = MongoClient("mongodb+srv://xpertdev:eE2g9lcdACyoifcf@xpert.sz91i4v.mongodb.net/?retryWrites=true&w=majority&appName=xpert")  # Replace with actual Mongo URI
db = client["bot_xpert"]
collection = db["token_state"]

SECRET_API_KEY = "redefine_kavach_4f8e2b7c9a1d4e6f8b2c3d5e7f9a0b1c"
ALLOWED_CLIENT_ID = "cli_aimguard_01F8MECHZX3TBDSZ7XRADM79XE"
ALLOWED_USER_AGENTS = ["Kavach/1.0.0", "Aimguard/1.0.0"]
ALLOWED_REQUEST_TYPE = "redefine-like"

# Region config
REGION_CONFIG = {
    "IND": {
        "tokens": "ind_tokens",
        "url": "https://client.ind.freefiremobile.com/LikeProfile",
        "state": "IND"
    },
    "NX": {
        "tokens": "nx_tokens", 
        "url": "https://client.us.freefiremobile.com/LikeProfile",
        "state": "NX"
    },
    "AG": {
        "tokens": "ag_tokens",
        "url": "https://clientbp.ggblueshark.com/LikeProfile", 
        "state": "AG"
    }
}

@app.route("/")
def home():
    return "API is Alive with new!", 200

@app.route("/like", methods=["GET"])
def handle_requests():
    # Extract headers
    api_key = request.headers.get("X-API-KEY")
    client_id = request.headers.get("X-CLIENT-ID")
    user_agent = request.headers.get("User-Agent")
    request_type = request.headers.get("X-REQUEST-TYPE")

    if (
        api_key != SECRET_API_KEY or
        client_id != ALLOWED_CLIENT_ID or
        user_agent not in ALLOWED_USER_AGENTS or
        request_type != ALLOWED_REQUEST_TYPE
    ):
        return jsonify({"error": "bad request / method not allowed"}), 400

    uid = request.args.get("uid")
    region = request.args.get("region", "").upper()

    if not uid or region not in REGION_CONFIG:
        return jsonify({"error": "UID required and region must be IND, NX, or AG"}), 400

    try:
        def process_request():
            config = REGION_CONFIG[region]
            tokens_collection = db[config["tokens"]]

            tokens_cursor = tokens_collection.find({}, {"_id": 0, "token": 1})
            tokens = list(tokens_cursor)

            if not tokens:
                raise Exception(f"No tokens available in {config['tokens']}.")

            token = tokens[0]["token"]
            encrypted_uid = enc(uid)

            before = make_request(encrypted_uid, region, token)
            if before is None:
                raise Exception("Failed to retrieve initial player info.")

            data_before = json.loads(MessageToJson(before))
            before_like = int(data_before.get("AccountInfo", {}).get("Likes", 0))
            player_region = str(data_before.get("AccountInfo", {}).get("region", ""))

            url = config["url"]
            asyncio.run(send_multiple_requests(uid, region, url, tokens))

            after = make_request(encrypted_uid, region, token)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")

            data_after = json.loads(MessageToJson(after))
            player_uid = int(data_after.get("AccountInfo", {}).get("UID", 0))
            after_like = int(data_after.get("AccountInfo", {}).get("Likes", 0))
            player_name = str(data_after.get("AccountInfo", {}).get("PlayerNickname", ""))
            like_given = after_like - before_like
            status = 1 if like_given != 0 else 2

            token_state_region = config["state"]

            if status == 1:
                collection.update_one(
                    {"region": token_state_region},
                    {"$inc": {"success_count": 1}},
                    upsert=True
                )

            doc = collection.find_one({"region": token_state_region}, {"success_count": 1})
            success_count = doc.get("success_count", 0) if doc else 0

            return {
                "status": status,
                "message": "Like operation successful" if status == 1 else "No likes added",
                "player": {
                    "uid": player_uid,
                    "region" : player_region,
                    "nickname": player_name
                },
                "likes": {
                    "before": before_like,
                    "after": after_like,
                    "added_by_api": like_given
                },
                "success_count": success_count,
                "token_collection_used": config["tokens"],
                "token_state_region": token_state_region
            }

        result = process_request()
        return Response(json.dumps(result, indent=2, sort_keys=False), mimetype="application/json")
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

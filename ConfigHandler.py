import uuid
import time
import json
import base64
import aiohttp

API_URL = "http://127.0.0.1:62789/addUser"
SERVER_ADDR = "103.75.199.67"
SERVER_PORT = 443
USE_TLS = True
PROTOCOL = "vmess"

async def create_trial_user_api(email_or_id: str, hours: int = 24, traffic_bytes: int = 1073741824):
    uid = str(uuid.uuid4())
    expiry_ms = int(time.time() * 1000) + hours * 3600 * 1000

    payload = {
        "user": email_or_id,
        "uuid": uid,
        "expiry": expiry_ms,
        "traffic": traffic_bytes
    }

    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post(API_URL, json=payload, timeout=10) as resp:
                text = await resp.text()
                if resp.status not in (200, 201):
                    return {"error": f"API returned {resp.status}: {text}"}

                try:
                    data = await resp.json()
                except Exception:
                    data = {"raw": text}

                vmess_obj = {
                    "v": "2",
                    "ps": f"Trial-{email_or_id}",
                    "add": SERVER_ADDR,
                    "port": str(SERVER_PORT),
                    "id": uid,
                    "aid": "0",
                    "net": "ws",
                    "type": "none",
                    "host": "",
                    "path": "/",
                    "tls": "tls" if USE_TLS else ""
                }
                vmess_b64 = base64.b64encode(json.dumps(vmess_obj, separators=(",", ":")).encode()).decode()
                vmess_link = f"vmess://{vmess_b64}"

                return {"uuid": uid, "link": vmess_link, "api_response": data}

    except Exception as e:
        return {"error": str(e)}

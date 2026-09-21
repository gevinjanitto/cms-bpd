import hashlib
import json
import os
from pathlib import Path

import requests
from pymongo import MongoClient


def read_env_value(file_path: str, key: str):
    path = Path(file_path)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return None


base_url = os.environ.get("REACT_APP_BACKEND_URL") or read_env_value("/app/frontend/.env", "REACT_APP_BACKEND_URL")
mongo_url = os.environ.get("MONGO_URL") or read_env_value("/app/backend/.env", "MONGO_URL")
db_name = os.environ.get("DB_NAME") or read_env_value("/app/backend/.env", "DB_NAME")

if not all([base_url, mongo_url, db_name]):
    raise RuntimeError("Missing REACT_APP_BACKEND_URL/MONGO_URL/DB_NAME")

client = requests.Session()
db = MongoClient(mongo_url)[db_name]

tokens = {}
for username in ["admin", "supervisor", "karyawan", "direksi"]:
    captcha = client.get(f"{base_url.rstrip('/')}/api/auth/captcha", timeout=30).json()
    answer_hash = hashlib.sha256(f"{captcha['id']}:TESTAB".encode()).hexdigest()
    db.captchas.update_one({"id": captcha["id"]}, {"$set": {"answer_hash": answer_hash}})
    login = client.post(
        f"{base_url.rstrip('/')}/api/auth/login",
        json={
            "username": username,
            "password": "bpdjaya3x",
            "captcha_id": captcha["id"],
            "captcha_answer": "TESTAB",
        },
        timeout=30,
    )
    login.raise_for_status()
    payload = login.json()
    tokens[username] = {"token": payload["token"], "role": payload["user"]["role"], "name": payload["user"]["name"]}

output_path = Path("/app/test_reports/artifacts_iter2/tokens.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(tokens), encoding="utf-8")
print(str(output_path))

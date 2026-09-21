import csv
import hashlib
import io
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest
import requests
from PIL import Image
from openpyxl import load_workbook
from pymongo import MongoClient


def _read_env_value(file_path: str, key: str):
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


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or _read_env_value("/app/frontend/.env", "REACT_APP_BACKEND_URL")
MONGO_URL = os.environ.get("MONGO_URL") or _read_env_value("/app/backend/.env", "MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or _read_env_value("/app/backend/.env", "DB_NAME")


@pytest.fixture(scope="session")
def base_url():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL is not configured")
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def client():
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    return session


@pytest.fixture(scope="session")
def mongo_db():
    if not MONGO_URL or not DB_NAME:
        pytest.skip("MONGO_URL/DB_NAME not configured for captcha-fixture tests")
    mongo_client = MongoClient(MONGO_URL)
    yield mongo_client[DB_NAME]
    mongo_client.close()


def _issue_captcha(client, base_url):
    response = client.get(f"{base_url}/api/auth/captcha", timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("id"), str) and payload["id"]
    assert isinstance(payload.get("image"), str) and payload["image"].startswith("data:image/png;base64,")
    assert payload.get("expires_in") == 180
    return payload


def _seed_captcha_answer(mongo_db, captcha_id, answer="TESTAB"):
    digest = hashlib.sha256(f"{captcha_id}:{answer}".encode()).hexdigest()
    mongo_db.captchas.update_one({"id": captcha_id}, {"$set": {"answer_hash": digest}})


def _login(client, base_url, username, password, captcha_id, captcha_answer):
    return client.post(
        f"{base_url}/api/auth/login",
        json={
            "username": username,
            "password": password,
            "captcha_id": captcha_id,
            "captcha_answer": captcha_answer,
        },
        timeout=30,
    )


def _auth_headers(client, base_url, mongo_db, username="admin", password="bpdjaya3x"):
    captcha = _issue_captcha(client, base_url)
    _seed_captcha_answer(mongo_db, captcha["id"], "TESTAB")
    login = _login(client, base_url, username, password, captcha["id"], "TESTAB")
    assert login.status_code == 200
    data = login.json()
    assert isinstance(data.get("token"), str) and data["token"]
    return {"Authorization": f"Bearer {data['token']}"}, data


# Auth + captcha contract coverage
def test_health_and_demo_endpoint_removed(client, base_url):
    health = client.get(f"{base_url}/api/health", timeout=30)
    assert health.status_code == 200
    assert health.json().get("status") == "ok"

    demo = client.post(f"{base_url}/api/auth/demo", json={"role": "administrator"}, timeout=30)
    assert demo.status_code == 404


def test_captcha_login_success_and_session_persistence(client, base_url, mongo_db):
    headers, login_data = _auth_headers(client, base_url, mongo_db, username="admin", password="bpdjaya3x")
    assert login_data["user"]["role"] == "administrator"

    me = client.get(f"{base_url}/api/auth/me", headers=headers, timeout=30)
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["role"] == "administrator"
    assert me_data["id"] == login_data["user"]["id"]
    assert "password_hash" not in me_data


def test_captcha_wrong_reuse_and_password_lockout(client, base_url, mongo_db):
    mongo_db.credentials.update_one(
        {"username": "direksi"},
        {"$set": {"failed_attempts": 0}, "$unset": {"locked_until": ""}},
    )


def test_captcha_expiration_and_change_password_restore(client, base_url, mongo_db):
    expired = _issue_captcha(client, base_url)
    _seed_captcha_answer(mongo_db, expired["id"], "TESTAB")
    mongo_db.captchas.update_one(
        {"id": expired["id"]},
        {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(seconds=5)}},
    )
    expired_login = _login(client, base_url, "admin", "bpdjaya3x", expired["id"], "TESTAB")
    assert expired_login.status_code == 400

    headers, _ = _auth_headers(client, base_url, mongo_db, username="admin", password="bpdjaya3x")
    temp_password = "bpdjaya3xTmp"
    changed = client.post(
        f"{base_url}/api/auth/change-password",
        headers={**headers, "Content-Type": "application/json"},
        json={"current_password": "bpdjaya3x", "new_password": temp_password},
        timeout=30,
    )
    assert changed.status_code == 200

    try:
        temp_headers, _ = _auth_headers(client, base_url, mongo_db, username="admin", password=temp_password)
        restored = client.post(
            f"{base_url}/api/auth/change-password",
            headers={**temp_headers, "Content-Type": "application/json"},
            json={"current_password": temp_password, "new_password": "bpdjaya3x"},
            timeout=30,
        )
        assert restored.status_code == 200
    except Exception:
        # best-effort recovery if temp login path fails unexpectedly
        challenge = _issue_captcha(client, base_url)
        _seed_captcha_answer(mongo_db, challenge["id"], "TESTAB")
        retry = _login(client, base_url, "admin", temp_password, challenge["id"], "TESTAB")
        if retry.status_code == 200:
            token = retry.json()["token"]
            client.post(
                f"{base_url}/api/auth/change-password",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"current_password": temp_password, "new_password": "bpdjaya3x"},
                timeout=30,
            )
        raise

    wrong = _issue_captcha(client, base_url)
    wrong_login = _login(client, base_url, "direksi", "bpdjaya3x", wrong["id"], "WRONG1")
    assert wrong_login.status_code == 400

    valid = _issue_captcha(client, base_url)
    _seed_captcha_answer(mongo_db, valid["id"], "TESTAB")
    first = _login(client, base_url, "supervisor", "bpdjaya3x", valid["id"], "TESTAB")
    assert first.status_code == 200
    reused = _login(client, base_url, "supervisor", "bpdjaya3x", valid["id"], "TESTAB")
    assert reused.status_code == 400

    for _ in range(3):
        challenge = _issue_captcha(client, base_url)
        _seed_captcha_answer(mongo_db, challenge["id"], "TESTAB")
        failed = _login(client, base_url, "direksi", "salah-password", challenge["id"], "TESTAB")
        assert failed.status_code == 401

    challenge = _issue_captcha(client, base_url)
    _seed_captcha_answer(mongo_db, challenge["id"], "TESTAB")
    locked = _login(client, base_url, "direksi", "bpdjaya3x", challenge["id"], "TESTAB")
    assert locked.status_code == 423

    mongo_db.credentials.update_one(
        {"username": "direksi"},
        {"$set": {"failed_attempts": 0}, "$unset": {"locked_until": ""}},
    )


# Report export and storage integration coverage
def test_export_csv_and_xlsx_structure(client, base_url, mongo_db):
    headers, _ = _auth_headers(client, base_url, mongo_db, username="admin", password="bpdjaya3x")

    csv_response = client.get(
        f"{base_url}/api/reports/export",
        params={"format": "csv", "view": "results", "period": "2026"},
        headers=headers,
        timeout=60,
    )
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers.get("content-type", "")

    csv_text = csv_response.content.decode("utf-8")
    assert csv_text.startswith("\ufeffsep=;\r\n")
    lines = csv_text.lstrip("\ufeff").splitlines()
    assert lines[0] == "sep=;"
    parsed = list(csv.reader(lines[1:], delimiter=";"))
    assert len(parsed) >= 2

    expected_columns = len(parsed[0])
    assert all(len(row) == expected_columns for row in parsed[1:])
    assert "Status" in parsed[0]
    status_idx = parsed[0].index("Status")
    status_values = {row[status_idx] for row in parsed[1:] if len(row) > status_idx and row[status_idx]}
    assert status_values.issubset({"Lulus", "Belum Lulus", "Menunggu Penilaian", "Belum Mengikuti"})

    if "Waktu Pengumpulan (WITA)" in parsed[0]:
        date_idx = parsed[0].index("Waktu Pengumpulan (WITA)")
        date_values = [row[date_idx] for row in parsed[1:] if len(row) > date_idx and row[date_idx]]
        assert all("T" not in value and len(value.split("/")) == 3 for value in date_values)

    xlsx_response = client.get(
        f"{base_url}/api/reports/export",
        params={"format": "xlsx", "view": "results", "period": "2026"},
        headers=headers,
        timeout=60,
    )
    assert xlsx_response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in xlsx_response.headers.get("content-type", "")

    workbook = load_workbook(io.BytesIO(xlsx_response.content))
    sheet = workbook.active
    assert sheet.title == "Laporan Kepatuhan"
    assert str(sheet["A1"].value).startswith("COMPLIANCE MANAGEMENT SYSTEM")
    assert sheet.freeze_panes == "A6"
    assert sheet.auto_filter.ref is not None


# Media status and user-data leakage coverage
def test_media_status_branding_and_user_payload_safety(client, base_url, mongo_db):
    headers, _ = _auth_headers(client, base_url, mongo_db, username="admin", password="bpdjaya3x")

    media = client.get(f"{base_url}/api/media/status", headers=headers, timeout=30)
    assert media.status_code == 200
    media_data = media.json()
    assert media_data["cloudinary_configured"] is False
    assert media_data["documents_storage"] == "MongoDB GridFS"

    branding = client.get(f"{base_url}/api/branding", timeout=30)
    assert branding.status_code == 200
    branding_data = branding.json()
    assert "logo_url" in branding_data and "login_image_url" in branding_data

    png_buffer = io.BytesIO()
    Image.new("RGB", (1, 1), "#1a7c57").save(png_buffer, format="PNG")
    tiny_png = png_buffer.getvalue()
    image_upload = client.post(
        f"{base_url}/api/media/images?purpose=library",
        headers=headers,
        files={"file": ("tiny.png", tiny_png, "image/png")},
        timeout=30,
    )
    assert image_upload.status_code == 503

    users = client.get(f"{base_url}/api/users", headers=headers, timeout=30)
    assert users.status_code == 200
    values = users.json()
    assert isinstance(values, list) and values
    leaked_keys = [k for row in values for k in row.keys() if "password" in k.lower()]
    assert not leaked_keys

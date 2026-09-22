"""Regression tests for contact settings security and regulasi route compatibility."""

import hashlib
import os
from pathlib import Path

import pytest
import requests
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
        pytest.skip("MONGO_URL/DB_NAME not configured")
    mongo_client = MongoClient(MONGO_URL)
    yield mongo_client[DB_NAME]
    mongo_client.close()


def _issue_captcha(client, base_url):
    response = client.get(f"{base_url}/api/auth/captcha", timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("id"), str) and payload["id"]
    return payload


def _seed_captcha_answer(mongo_db, captcha_id, answer="TESTAB"):
    digest = hashlib.sha256(f"{captcha_id}:{answer}".encode()).hexdigest()
    mongo_db.captchas.update_one({"id": captcha_id}, {"$set": {"answer_hash": digest}})


def _login(client, base_url, mongo_db, username, password):
    captcha = _issue_captcha(client, base_url)
    _seed_captcha_answer(mongo_db, captcha["id"], "TESTAB")
    response = client.post(
        f"{base_url}/api/auth/login",
        json={
            "username": username,
            "password": password,
            "captcha_id": captcha["id"],
            "captcha_answer": "TESTAB",
        },
        timeout=30,
    )
    return response


def _auth_headers(client, base_url, mongo_db, username, password):
    login = _login(client, base_url, mongo_db, username, password)
    assert login.status_code == 200
    payload = login.json()
    assert isinstance(payload.get("token"), str) and payload["token"]
    return {"Authorization": f"Bearer {payload['token']}"}, payload


def _admin_put_settings(client, base_url, mongo_db, body):
    headers, _ = _auth_headers(client, base_url, mongo_db, "admin", "bpdjaya3x")
    return client.put(
        f"{base_url}/api/settings",
        headers={**headers, "Content-Type": "application/json"},
        json=body,
        timeout=30,
    )


# Contact public endpoint contract
def test_public_contact_returns_allowlist_only(client, base_url):
    response = client.get(f"{base_url}/api/settings/contact", timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"contact_label", "contact_url"}
    assert isinstance(data["contact_label"], str)
    assert isinstance(data["contact_url"], str)


# Authorization contract for settings update
def test_put_settings_requires_admin(client, base_url, mongo_db):
    current = client.get(f"{base_url}/api/settings/contact", timeout=30).json()

    unauth = client.put(
        f"{base_url}/api/settings",
        json={
            "passing_grade": 75,
            "quiz_duration": 30,
            "idle_timeout": 300,
            "contact_label": current["contact_label"],
            "contact_url": current["contact_url"],
        },
        timeout=30,
    )
    assert unauth.status_code == 401

    employee_headers, _ = _auth_headers(client, base_url, mongo_db, "karyawan", "bpdjaya3x")
    forbidden = client.put(
        f"{base_url}/api/settings",
        headers={**employee_headers, "Content-Type": "application/json"},
        json={
            "passing_grade": 75,
            "quiz_duration": 30,
            "idle_timeout": 300,
            "contact_label": current["contact_label"],
            "contact_url": current["contact_url"],
        },
        timeout=30,
    )
    assert forbidden.status_code == 403


# Contact URL validation allowlist/denylist
def test_put_settings_contact_validation_and_persistence(client, base_url, mongo_db):
    admin_headers, _ = _auth_headers(client, base_url, mongo_db, "admin", "bpdjaya3x")
    settings_before = client.get(f"{base_url}/api/settings", headers=admin_headers, timeout=30)
    assert settings_before.status_code == 200
    before = settings_before.json()

    invalid_urls = [
        "javascript:alert(1)",
        "data:text/html;base64,PHNjcmlwdD4=",
        "/relative/path",
        "https://exa mple.com",
        "http://user:pass@example.com",
        "https://example.com%0Afoo",
    ]
    for value in invalid_urls:
        bad = _admin_put_settings(
            client,
            base_url,
            mongo_db,
            {
                "passing_grade": before["passing_grade"],
                "quiz_duration": before["quiz_duration"],
                "idle_timeout": before["idle_timeout"],
                "contact_label": "Hubungi administrator SISDUR.",
                "contact_url": value,
            },
        )
        assert bad.status_code == 422

    bad_label_blank = _admin_put_settings(
        client,
        base_url,
        mongo_db,
        {
            "passing_grade": before["passing_grade"],
            "quiz_duration": before["quiz_duration"],
            "idle_timeout": before["idle_timeout"],
            "contact_label": "   ",
            "contact_url": "",
        },
    )
    assert bad_label_blank.status_code == 422

    too_long_label = "X" * 121
    bad_label_long = _admin_put_settings(
        client,
        base_url,
        mongo_db,
        {
            "passing_grade": before["passing_grade"],
            "quiz_duration": before["quiz_duration"],
            "idle_timeout": before["idle_timeout"],
            "contact_label": too_long_label,
            "contact_url": "",
        },
    )
    assert bad_label_long.status_code == 422

    allowed_urls = [
        "https://www.maiharta.com",
        "http://example.org/path",
        "mailto:test@example.com",
        "tel:+628123456789",
    ]
    for value in allowed_urls:
        good = _admin_put_settings(
            client,
            base_url,
            mongo_db,
            {
                "passing_grade": before["passing_grade"],
                "quiz_duration": before["quiz_duration"],
                "idle_timeout": before["idle_timeout"],
                "contact_label": "TEST_CONTACT_LABEL",
                "contact_url": value,
            },
        )
        assert good.status_code == 200
        saved = good.json()
        assert saved["contact_label"] == "TEST_CONTACT_LABEL"
        assert saved["contact_url"] == value

        public_contact = client.get(f"{base_url}/api/settings/contact", timeout=30)
        assert public_contact.status_code == 200
        public_data = public_contact.json()
        assert public_data["contact_label"] == "TEST_CONTACT_LABEL"
        assert public_data["contact_url"] == value
        assert set(public_data.keys()) == {"contact_label", "contact_url"}

    label_only = _admin_put_settings(
        client,
        base_url,
        mongo_db,
        {
            "passing_grade": before["passing_grade"],
            "quiz_duration": before["quiz_duration"],
            "idle_timeout": before["idle_timeout"],
            "contact_label": "Hubungi administrator SISDUR.",
            "contact_url": "",
        },
    )
    assert label_only.status_code == 200
    assert label_only.json()["contact_url"] == ""

    numeric_only = _admin_put_settings(
        client,
        base_url,
        mongo_db,
        {
            "passing_grade": before["passing_grade"],
            "quiz_duration": before["quiz_duration"],
            "idle_timeout": before["idle_timeout"],
        },
    )
    assert numeric_only.status_code == 200
    numeric_data = numeric_only.json()
    assert numeric_data["passing_grade"] == before["passing_grade"]
    assert numeric_data["quiz_duration"] == before["quiz_duration"]
    assert numeric_data["idle_timeout"] == before["idle_timeout"]
    assert isinstance(numeric_data.get("contact_label"), str)
    assert isinstance(numeric_data.get("contact_url"), str)
    assert "_id" not in numeric_data

    restore = _admin_put_settings(
        client,
        base_url,
        mongo_db,
        {
            "passing_grade": before["passing_grade"],
            "quiz_duration": before["quiz_duration"],
            "idle_timeout": before["idle_timeout"],
            "contact_label": before["contact_label"],
            "contact_url": before["contact_url"],
        },
    )
    assert restore.status_code == 200
    restored = restore.json()
    assert restored["contact_label"] == before["contact_label"]
    assert restored["contact_url"] == before["contact_url"]


# Legacy route compatibility
def test_legacy_ketentuan_route_redirects(client, base_url):
    response = client.get(
        f"{base_url}/ketentuan?q=abc&status=published",
        allow_redirects=False,
        headers={"Accept": "text/html"},
        timeout=30,
    )
    assert response.status_code == 200
    assert "<!doctype html>" in response.text.lower()

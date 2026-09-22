"""Regression tests for document activation rules, visibility, dashboard impact, and quiz guards."""

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


@pytest.fixture(scope="session")
def role_headers(client, base_url, mongo_db):
    def _for(username: str, password: str = "bpdjaya3x"):
        captcha = client.get(f"{base_url}/api/auth/captcha", timeout=30)
        assert captcha.status_code == 200
        captcha_id = captcha.json()["id"]
        digest = hashlib.sha256(f"{captcha_id}:TESTAB".encode()).hexdigest()
        mongo_db.captchas.update_one({"id": captcha_id}, {"$set": {"answer_hash": digest}})
        login = client.post(
            f"{base_url}/api/auth/login",
            json={
                "username": username,
                "password": password,
                "captcha_id": captcha_id,
                "captcha_answer": "TESTAB",
            },
            timeout=30,
        )
        assert login.status_code == 200
        token = login.json()["token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    return {
        "admin": _for("admin"),
        "supervisor": _for("supervisor"),
        "employee": _for("karyawan"),
        "director": _for("direksi"),
    }


@pytest.fixture()
def cleanup_ids(mongo_db):
    tracker = {"doc_ids": [], "quiz_ids": []}
    yield tracker
    if tracker["quiz_ids"]:
        mongo_db.quizzes.update_many({"id": {"$in": tracker["quiz_ids"]}}, {"$set": {"is_deleted": True}})
    if tracker["doc_ids"]:
        mongo_db.documents.update_many({"id": {"$in": tracker["doc_ids"]}}, {"$set": {"is_deleted": True}})


def _create_doc(client, base_url, admin_headers, title_suffix=""):
    payload = {
        "title": f"TEST_ACT_{title_suffix}",
        "number": f"TEST/ACT/{title_suffix}",
        "category": "Internal",
        "unit": "Divisi Kepatuhan",
        "description": "TEST activation flow",
        "version": "1.0",
    }
    response = client.post(f"{base_url}/api/documents", headers=admin_headers, json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["is_active"] is True
    assert "_id" not in data
    return data


def _set_sample_and_publish(client, base_url, mongo_db, headers, doc_id):
    mongo_db.documents.update_one({"id": doc_id}, {"$set": {"sample": True, "updated_at": "2026-01-01T00:00:00+00:00"}})
    submit = client.post(
        f"{base_url}/api/documents/{doc_id}/action",
        headers=headers["admin"],
        json={"action": "submit", "reason": ""},
        timeout=30,
    )
    assert submit.status_code == 200
    approve = client.post(
        f"{base_url}/api/documents/{doc_id}/action",
        headers=headers["supervisor"],
        json={"action": "approve", "reason": ""},
        timeout=30,
    )
    assert approve.status_code == 200
    return approve.json()


def _create_quiz(client, base_url, admin_headers, document_id, suffix=""):
    payload = {
        "title": f"TEST Quiz {suffix}",
        "description": "TEST",
        "document_id": document_id,
        "passing_grade": 75,
        "duration": 30,
        "units": [],
        "positions": [],
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "questions": [
            {
                "id": f"q-{suffix}",
                "text": "Pilihan benar?",
                "type": "multiple",
                "options": ["A", "B", "C", "D"],
                "correct": 1,
            }
        ],
    }
    response = client.post(f"{base_url}/api/quizzes", headers=admin_headers, json=payload, timeout=30)
    return response


# Activation authorization + schema validation
def test_activation_requires_admin_and_strictbool(client, base_url, role_headers, cleanup_ids):
    doc = _create_doc(client, base_url, role_headers["admin"], "AUTH")
    cleanup_ids["doc_ids"].append(doc["id"])

    unauth = client.put(f"{base_url}/api/documents/{doc['id']}/activation", json={"is_active": False}, timeout=30)
    assert unauth.status_code == 401

    for role in ("supervisor", "employee", "director"):
        forbidden = client.put(
            f"{base_url}/api/documents/{doc['id']}/activation",
            headers=role_headers[role],
            json={"is_active": False},
            timeout=30,
        )
        assert forbidden.status_code == 403

    bad_string = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": "false"},
        timeout=30,
    )
    assert bad_string.status_code == 422

    missing = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={},
        timeout=30,
    )
    assert missing.status_code == 422


# Activation record existence + response shape
def test_activation_missing_and_deleted_document_returns_404(client, base_url, role_headers, mongo_db, cleanup_ids):
    not_found = client.put(
        f"{base_url}/api/documents/does-not-exist/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert not_found.status_code == 404

    doc = _create_doc(client, base_url, role_headers["admin"], "DELETED")
    cleanup_ids["doc_ids"].append(doc["id"])
    mongo_db.documents.update_one({"id": doc["id"]}, {"$set": {"is_deleted": True}})

    deleted = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deleted.status_code == 404


# Idempotent activation audit + metadata preservation
def test_activation_toggle_preserves_fields_and_audit_is_idempotent(client, base_url, role_headers, mongo_db, cleanup_ids):
    doc = _create_doc(client, base_url, role_headers["admin"], "IDEMP")
    cleanup_ids["doc_ids"].append(doc["id"])
    # Ensure stored file metadata exists and status published
    mongo_db.documents.update_one(
        {"id": doc["id"]},
        {
            "$set": {
                "status": "published",
                "sample": True,
                "filename": "test-file.pdf",
                "content_type": "application/pdf",
                "file_size": 12345,
                "storage_path": "cms-bali-dwipa/uploads/demo/test-file.pdf",
            }
        },
    )

    before = client.get(f"{base_url}/api/audit", headers=role_headers["admin"], params={"module": "Regulasi", "q": doc["title"]}, timeout=30)
    assert before.status_code == 200
    before_rows = before.json()
    before_deactivate = sum(1 for r in before_rows if r.get("action") == "DEACTIVATE")
    before_activate = sum(1 for r in before_rows if r.get("action") == "ACTIVATE")

    deactivate = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deactivate.status_code == 200
    de_data = deactivate.json()
    assert de_data["is_active"] is False
    assert de_data["status"] == "published"
    assert de_data["filename"] == "test-file.pdf"
    assert de_data["content_type"] == "application/pdf"
    assert de_data["file_size"] == 12345
    assert "_id" not in de_data
    assert "storage_path" not in de_data

    deactivate_repeat = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deactivate_repeat.status_code == 200
    assert deactivate_repeat.json()["is_active"] is False

    reactivate = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": True},
        timeout=30,
    )
    assert reactivate.status_code == 200
    assert reactivate.json()["is_active"] is True

    reactivate_repeat = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": True},
        timeout=30,
    )
    assert reactivate_repeat.status_code == 200
    assert reactivate_repeat.json()["is_active"] is True

    after = client.get(f"{base_url}/api/audit", headers=role_headers["admin"], params={"module": "Regulasi", "q": doc["title"]}, timeout=30)
    assert after.status_code == 200
    after_rows = after.json()
    after_deactivate = sum(1 for r in after_rows if r.get("action") == "DEACTIVATE")
    after_activate = sum(1 for r in after_rows if r.get("action") == "ACTIVATE")
    assert after_deactivate == before_deactivate + 1
    assert after_activate == before_activate + 1


# Visibility and download access for inactive docs
def test_inactive_visibility_and_download_permissions(client, base_url, role_headers, mongo_db, cleanup_ids):
    doc = _create_doc(client, base_url, role_headers["admin"], "VIS")
    cleanup_ids["doc_ids"].append(doc["id"])
    _set_sample_and_publish(client, base_url, mongo_db, role_headers, doc["id"])

    deactivate = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deactivate.status_code == 200

    admin_inactive = client.get(
        f"{base_url}/api/documents",
        headers=role_headers["admin"],
        params={"active": "false"},
        timeout=30,
    )
    assert admin_inactive.status_code == 200
    admin_ids = {d["id"] for d in admin_inactive.json()}
    assert doc["id"] in admin_ids

    employee_inactive_query = client.get(
        f"{base_url}/api/documents",
        headers=role_headers["employee"],
        params={"active": "false"},
        timeout=30,
    )
    assert employee_inactive_query.status_code == 200
    employee_inactive_ids = {d["id"] for d in employee_inactive_query.json()}
    assert doc["id"] not in employee_inactive_ids

    employee_default = client.get(f"{base_url}/api/documents", headers=role_headers["employee"], timeout=30)
    assert employee_default.status_code == 200
    assert doc["id"] not in {d["id"] for d in employee_default.json()}

    denied_download = client.get(f"{base_url}/api/documents/{doc['id']}/download", headers=role_headers["employee"], timeout=30)
    assert denied_download.status_code == 403

    admin_download = client.get(f"{base_url}/api/documents/{doc['id']}/download", headers=role_headers["admin"], timeout=30)
    assert admin_download.status_code == 200


# Dashboard counts + stale action guard when inactive
def test_inactive_excluded_from_dashboard_and_stale_actions_rejected(client, base_url, role_headers, mongo_db, cleanup_ids):
    before_dashboard = client.get(f"{base_url}/api/dashboard", headers=role_headers["admin"], timeout=30)
    assert before_dashboard.status_code == 200
    before = before_dashboard.json()["tasks"]["documents"]

    doc = _create_doc(client, base_url, role_headers["admin"], "DASH")
    cleanup_ids["doc_ids"].append(doc["id"])
    mongo_db.documents.update_one({"id": doc["id"]}, {"$set": {"sample": True}})

    submitted = client.post(
        f"{base_url}/api/documents/{doc['id']}/action",
        headers=role_headers["admin"],
        json={"action": "submit", "reason": ""},
        timeout=30,
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "pending"

    pending_dash = client.get(f"{base_url}/api/dashboard", headers=role_headers["admin"], timeout=30)
    assert pending_dash.status_code == 200
    pending_tasks = pending_dash.json()["tasks"]["documents"]
    assert pending_tasks >= before + 1

    deactivate = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deactivate.status_code == 200

    blocked_submit = client.post(
        f"{base_url}/api/documents/{doc['id']}/action",
        headers=role_headers["admin"],
        json={"action": "submit", "reason": ""},
        timeout=30,
    )
    assert blocked_submit.status_code == 409

    stale_approve = client.post(
        f"{base_url}/api/documents/{doc['id']}/action",
        headers=role_headers["supervisor"],
        json={"action": "approve", "reason": ""},
        timeout=30,
    )
    assert stale_approve.status_code == 409

    stale_reject = client.post(
        f"{base_url}/api/documents/{doc['id']}/action",
        headers=role_headers["supervisor"],
        json={"action": "reject", "reason": "Stale"},
        timeout=30,
    )
    assert stale_reject.status_code == 409

    hidden_dash = client.get(f"{base_url}/api/dashboard", headers=role_headers["admin"], timeout=30)
    assert hidden_dash.status_code == 200
    assert hidden_dash.json()["tasks"]["documents"] <= pending_tasks - 1

    reactivate = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": True},
        timeout=30,
    )
    assert reactivate.status_code == 200
    restored_dash = client.get(f"{base_url}/api/dashboard", headers=role_headers["admin"], timeout=30)
    assert restored_dash.status_code == 200
    assert restored_dash.json()["tasks"]["documents"] >= hidden_dash.json()["tasks"]["documents"] + 1


# Quiz guards for inactive regulation links
def test_quiz_guards_reject_inactive_regulation_and_allow_after_reactivation(client, base_url, role_headers, mongo_db, cleanup_ids):
    doc = _create_doc(client, base_url, role_headers["admin"], "QUIZ")
    cleanup_ids["doc_ids"].append(doc["id"])
    _set_sample_and_publish(client, base_url, mongo_db, role_headers, doc["id"])

    quiz = _create_quiz(client, base_url, role_headers["admin"], doc["id"], "draft-1")
    assert quiz.status_code == 200
    quiz_id = quiz.json()["id"]
    cleanup_ids["quiz_ids"].append(quiz_id)

    deactivate = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deactivate.status_code == 200

    create_with_inactive = _create_quiz(client, base_url, role_headers["admin"], doc["id"], "inactive-create")
    assert create_with_inactive.status_code == 409

    edit_payload = quiz.json().copy()
    edit_payload["title"] = "TEST Quiz edited"
    edit_payload["document_id"] = doc["id"]
    edit_payload["start_date"] = "2026-01-01"
    edit_payload["end_date"] = "2026-12-31"
    edit_with_inactive = client.put(
        f"{base_url}/api/quizzes/{quiz_id}",
        headers=role_headers["admin"],
        json=edit_payload,
        timeout=30,
    )
    assert edit_with_inactive.status_code == 409

    submit_inactive = client.post(
        f"{base_url}/api/quizzes/{quiz_id}/action",
        headers=role_headers["admin"],
        json={"action": "submit", "reason": ""},
        timeout=30,
    )
    assert submit_inactive.status_code == 409

    reactivate = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": True},
        timeout=30,
    )
    assert reactivate.status_code == 200

    submit_after_reactivate = client.post(
        f"{base_url}/api/quizzes/{quiz_id}/action",
        headers=role_headers["admin"],
        json={"action": "submit", "reason": ""},
        timeout=30,
    )
    assert submit_after_reactivate.status_code == 200
    assert submit_after_reactivate.json()["status"] == "pending"

    deactivate_again = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deactivate_again.status_code == 200

    approve_pending_inactive = client.post(
        f"{base_url}/api/quizzes/{quiz_id}/action",
        headers=role_headers["supervisor"],
        json={"action": "approve", "reason": ""},
        timeout=30,
    )
    assert approve_pending_inactive.status_code == 409

    reactivate_again = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": True},
        timeout=30,
    )
    assert reactivate_again.status_code == 200

    approve_after_reactivate = client.post(
        f"{base_url}/api/quizzes/{quiz_id}/action",
        headers=role_headers["supervisor"],
        json={"action": "approve", "reason": ""},
        timeout=30,
    )
    assert approve_after_reactivate.status_code == 200
    assert approve_after_reactivate.json()["status"] == "published"

    deactivate_final = client.put(
        f"{base_url}/api/documents/{doc['id']}/activation",
        headers=role_headers["admin"],
        json={"is_active": False},
        timeout=30,
    )
    assert deactivate_final.status_code == 200

    employee_quizzes = client.get(f"{base_url}/api/quizzes", headers=role_headers["employee"], timeout=30)
    assert employee_quizzes.status_code == 200
    published_ids = {q["id"] for q in employee_quizzes.json()}
    assert quiz_id in published_ids


# Legacy records should be treated as active in API output
def test_legacy_document_without_is_active_treated_as_active(client, base_url, role_headers, mongo_db, cleanup_ids):
    doc = _create_doc(client, base_url, role_headers["admin"], "LEGACY")
    cleanup_ids["doc_ids"].append(doc["id"])
    mongo_db.documents.update_one({"id": doc["id"]}, {"$unset": {"is_active": ""}})

    admin_list = client.get(f"{base_url}/api/documents", headers=role_headers["admin"], timeout=30)
    assert admin_list.status_code == 200
    found = next((d for d in admin_list.json() if d["id"] == doc["id"]), None)
    assert found is not None
    assert found["is_active"] is True

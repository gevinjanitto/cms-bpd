import io
import os
import time
from datetime import date, timedelta

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")


@pytest.fixture(scope="session")
def base_url():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL is not set")
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


def auth_headers(client, base_url, role):
    r = client.post(f"{base_url}/api/auth/demo", json={"role": role}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("token"), str) and data["token"]
    assert data.get("user", {}).get("role") == role
    return {"Authorization": f"Bearer {data['token']}"}


def pick_published_document(client, base_url, headers):
    r = client.get(f"{base_url}/api/documents", headers=headers, timeout=30)
    assert r.status_code == 200
    docs = r.json()
    published = [d for d in docs if d.get("status") == "published"]
    assert published
    return published[0]


# Health and auth coverage
def test_health_and_demo_auth(client, base_url):
    health = client.get(f"{base_url}/api/health", timeout=30)
    assert health.status_code == 200
    assert health.json().get("status") == "ok"

    headers = auth_headers(client, base_url, "administrator")
    me = client.get(f"{base_url}/api/auth/me", headers=headers, timeout=30)
    assert me.status_code == 200
    me_json = me.json()
    assert me_json.get("role") == "administrator"
    assert "_id" not in me_json


# Dashboard and reporting coverage
def test_dashboard_filters_and_export(client, base_url):
    admin_headers = auth_headers(client, base_url, "administrator")

    dashboard_all = client.get(
        f"{base_url}/api/dashboard",
        params={"period": "2026", "unit": ""},
        headers=admin_headers,
        timeout=30,
    )
    assert dashboard_all.status_code == 200
    all_json = dashboard_all.json()
    all_metrics = all_json["metrics"]
    assert all_metrics["assigned"] == all_metrics["completed"] + all_metrics["pending"]
    assert isinstance(all_json.get("trend"), list)

    dashboard_unit = client.get(
        f"{base_url}/api/dashboard",
        params={"period": "2026", "unit": "Divisi Kepatuhan"},
        headers=admin_headers,
        timeout=30,
    )
    assert dashboard_unit.status_code == 200
    unit_metrics = dashboard_unit.json()["metrics"]
    assert unit_metrics["assigned"] == unit_metrics["completed"] + unit_metrics["pending"]
    assert unit_metrics["employees"] <= all_metrics["employees"]

    export = client.get(
        f"{base_url}/api/reports/export",
        params={"period": "2026", "unit": "Divisi Kepatuhan"},
        headers=admin_headers,
        timeout=30,
    )
    assert export.status_code == 200
    assert "text/csv" in export.headers.get("content-type", "")
    assert "attachment" in export.headers.get("content-disposition", "").lower()
    assert "Nama Karyawan" in export.text


# RBAC negative coverage
def test_rbac_employee_restricted_endpoints(client, base_url):
    employee_headers = auth_headers(client, base_url, "employee")

    doc_create = client.post(
        f"{base_url}/api/documents",
        headers={**employee_headers, "Content-Type": "application/json"},
        json={
            "title": "TEST_RBAC",
            "number": "TEST/RBAC/001",
            "category": "Internal",
            "unit": "Divisi Kepatuhan",
            "description": "TEST",
            "version": "1.0",
        },
        timeout=30,
    )
    assert doc_create.status_code == 403

    users_view = client.get(f"{base_url}/api/users", headers=employee_headers, timeout=30)
    assert users_view.status_code == 403

    settings_update = client.put(
        f"{base_url}/api/settings",
        headers={**employee_headers, "Content-Type": "application/json"},
        json={"passing_grade": 75, "idle_timeout": 180, "quiz_duration": 30},
        timeout=30,
    )
    assert settings_update.status_code == 403


def test_rbac_director_and_admin_restrictions(client, base_url):
    director_headers = auth_headers(client, base_url, "director")
    quizzes = client.get(f"{base_url}/api/quizzes", headers=director_headers, timeout=30)
    assert quizzes.status_code == 200
    assert quizzes.json()
    quiz_id = quizzes.json()[0]["id"]

    director_detail = client.get(f"{base_url}/api/quizzes/{quiz_id}", headers=director_headers, timeout=30)
    assert director_detail.status_code == 403

    admin_headers = auth_headers(client, base_url, "administrator")
    published_doc = pick_published_document(client, base_url, admin_headers)
    admin_approve = client.post(
        f"{base_url}/api/documents/{published_doc['id']}/action",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"action": "approve", "reason": ""},
        timeout=30,
    )
    assert admin_approve.status_code == 403


# Documents full lifecycle and upload validation coverage
def test_document_lifecycle_and_upload_rules(client, base_url):
    admin_headers = auth_headers(client, base_url, "administrator")
    supervisor_headers = auth_headers(client, base_url, "supervisor")
    employee_headers = auth_headers(client, base_url, "employee")
    now_key = int(time.time())

    create = client.post(
        f"{base_url}/api/documents",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={
            "title": f"TEST_DOC_{now_key}",
            "number": f"TEST/DOC/{now_key}",
            "category": "Internal",
            "unit": "Divisi Kepatuhan",
            "description": "Dokumen uji otomatis",
            "version": "1.0",
        },
        timeout=30,
    )
    assert create.status_code == 200
    created = create.json()
    doc_id = created["id"]
    assert created["status"] == "draft"

    invalid_ext = client.post(
        f"{base_url}/api/documents/{doc_id}/upload",
        headers=admin_headers,
        files={"file": ("bad.txt", io.BytesIO(b"hello"), "text/plain")},
        timeout=30,
    )
    assert invalid_ext.status_code == 400

    invalid_pdf_signature = client.post(
        f"{base_url}/api/documents/{doc_id}/upload",
        headers=admin_headers,
        files={"file": ("bad.pdf", io.BytesIO(b"NOTPDF"), "application/pdf")},
        timeout=30,
    )
    assert invalid_pdf_signature.status_code == 400

    too_large = client.post(
        f"{base_url}/api/documents/{doc_id}/upload",
        headers=admin_headers,
        files={"file": ("large.pdf", io.BytesIO(b"%PDF" + b"a" * (10 * 1024 * 1024 + 2)), "application/pdf")},
        timeout=60,
    )
    assert too_large.status_code == 400

    draft_check = client.get(f"{base_url}/api/documents", headers=admin_headers, timeout=30)
    assert draft_check.status_code == 200
    refreshed = next(d for d in draft_check.json() if d["id"] == doc_id)
    assert refreshed["status"] == "draft"

    valid_upload = client.post(
        f"{base_url}/api/documents/{doc_id}/upload",
        headers=admin_headers,
        files={"file": ("valid.pdf", io.BytesIO(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"), "application/pdf")},
        timeout=60,
    )
    assert valid_upload.status_code == 200
    assert valid_upload.json().get("success") is True

    submit = client.post(
        f"{base_url}/api/documents/{doc_id}/action",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"action": "submit", "reason": ""},
        timeout=30,
    )
    assert submit.status_code == 200
    assert submit.json().get("status") == "pending"

    approve = client.post(
        f"{base_url}/api/documents/{doc_id}/action",
        headers={**supervisor_headers, "Content-Type": "application/json"},
        json={"action": "approve", "reason": ""},
        timeout=30,
    )
    assert approve.status_code == 200
    assert approve.json().get("status") == "published"

    employee_docs = client.get(f"{base_url}/api/documents", headers=employee_headers, timeout=30)
    assert employee_docs.status_code == 200
    employee_ids = {d["id"] for d in employee_docs.json()}
    assert doc_id in employee_ids

    download = client.get(f"{base_url}/api/documents/{doc_id}/download", headers=employee_headers, timeout=60)
    assert download.status_code == 200
    assert len(download.content) > 0


# Quizzes workflow, answer security, one-attempt rule, and essay grading
def test_quiz_workflow_and_attempt_and_essay_grading(client, base_url):
    admin_headers = auth_headers(client, base_url, "administrator")
    supervisor_headers = auth_headers(client, base_url, "supervisor")
    employee_headers = auth_headers(client, base_url, "employee")
    now_key = int(time.time())

    doc = pick_published_document(client, base_url, admin_headers)
    start = date.today().isoformat()
    end = (date.today() + timedelta(days=7)).isoformat()

    create_quiz = client.post(
        f"{base_url}/api/quizzes",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={
            "title": f"TEST_QUIZ_{now_key}",
            "description": "Quiz uji otomatis",
            "document_id": doc["id"],
            "passing_grade": 75,
            "duration": 30,
            "units": ["Divisi Kepatuhan"],
            "positions": ["Officer"],
            "start_date": start,
            "end_date": end,
            "questions": [
                {
                    "id": "q1",
                    "text": "Soal PG 1",
                    "type": "multiple",
                    "options": ["A", "B", "C", "D"],
                    "correct": 1,
                },
                {
                    "id": "q2",
                    "text": "Soal PG 2",
                    "type": "multiple",
                    "options": ["A", "B", "C", "D"],
                    "correct": 2,
                },
                {
                    "id": "q3",
                    "text": "Soal Esai",
                    "type": "essay",
                    "options": [],
                    "correct": 0,
                },
            ],
        },
        timeout=30,
    )
    assert create_quiz.status_code == 200
    quiz = create_quiz.json()
    quiz_id = quiz["id"]
    assert quiz["status"] == "draft"

    submit_quiz = client.post(
        f"{base_url}/api/quizzes/{quiz_id}/action",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"action": "submit", "reason": ""},
        timeout=30,
    )
    assert submit_quiz.status_code == 200
    assert submit_quiz.json().get("status") == "pending"

    approve_quiz = client.post(
        f"{base_url}/api/quizzes/{quiz_id}/action",
        headers={**supervisor_headers, "Content-Type": "application/json"},
        json={"action": "approve", "reason": ""},
        timeout=30,
    )
    assert approve_quiz.status_code == 200
    assert approve_quiz.json().get("status") == "published"

    employee_detail = client.get(f"{base_url}/api/quizzes/{quiz_id}", headers=employee_headers, timeout=30)
    assert employee_detail.status_code == 200
    for q in employee_detail.json().get("questions", []):
        assert "correct" not in q

    start_quiz = client.post(f"{base_url}/api/quizzes/{quiz_id}/start", headers=employee_headers, timeout=30)
    assert start_quiz.status_code == 200
    assert "started_at" in start_quiz.json()

    submit_employee = client.post(
        f"{base_url}/api/quizzes/{quiz_id}/submit",
        headers={**employee_headers, "Content-Type": "application/json"},
        json={"answers": {"q1": 1, "q2": 2, "q3": "Jawaban esai uji"}},
        timeout=30,
    )
    assert submit_employee.status_code == 200
    result = submit_employee.json()
    assert result["status"] == "reviewing"
    assert result["score"] == 66.7

    second_start = client.post(f"{base_url}/api/quizzes/{quiz_id}/start", headers=employee_headers, timeout=30)
    assert second_start.status_code == 400

    grade = client.post(
        f"{base_url}/api/results/{result['id']}/grade",
        headers={**supervisor_headers, "Content-Type": "application/json"},
        json={"essay_scores": {"q3": 90}, "note": "Bagus"},
        timeout=30,
    )
    assert grade.status_code == 200
    grade_json = grade.json()
    assert grade_json.get("score") == 96.7
    assert grade_json.get("status") == "passed"

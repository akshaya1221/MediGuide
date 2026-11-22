from fastapi.testclient import TestClient
import fitz


def test_health(client: TestClient):
    assert client.get("/health").json()["status"] == "ok"


def test_register_login_and_dashboard(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["document_count"] == 0
    login = client.post("/api/v1/auth/login", json={"email": "patient@example.com", "password": "strong-pass-123"})
    assert login.status_code == 200


def test_document_requires_auth(client: TestClient):
    assert client.get("/api/v1/documents").status_code == 401


def test_rejects_unsupported_upload(client: TestClient, auth_headers: dict[str, str]):
    response = client.post("/api/v1/documents", headers=auth_headers, data={"doc_type": "other"}, files={"file": ("note.txt", b"not a medical document", "text/plain")})
    assert response.status_code == 415


def test_pdf_upload_runs_real_processing_pipeline(client: TestClient, auth_headers: dict[str, str]):
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Lab Report 12/11/2026\nHemoglobin 13.2 g/dL\nFollow up with your doctor after two weeks.\nThis report is for review.")
    response = client.post(
        "/api/v1/documents",
        headers=auth_headers,
        data={"doc_type": "lab_report"},
        files={"file": ("lab-report.pdf", pdf.tobytes(), "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["explanation"]["model_name"] == "local-safe-fallback"
    assert body["followups"]

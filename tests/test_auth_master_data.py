from __future__ import annotations

from tests.support import bootstrap_admin, create_catalog_item, create_patient, login, make_client


def test_auth_bootstrap_login_and_me(tmp_path):
    with make_client(tmp_path, "lis-auth.sqlite3") as client:
        headers, user = bootstrap_admin(client)
        login_headers, logged_user = login(client, username="admin", password="admin12345")

        assert login_headers["Authorization"].startswith("Bearer ")
        assert logged_user["username"] == "admin"

        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["id"] == user["id"]


def test_patient_and_catalog_endpoints_require_auth_and_persist(tmp_path):
    with make_client(tmp_path, "lis-master-data.sqlite3") as client:
        unauth_patient = client.post(
            "/api/v1/patients",
            json={"mrn": "MRN-001", "given_name": "Anna", "family_name": "Nowak"},
        )
        assert unauth_patient.status_code == 401

        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)

        patient_read = client.get(f"/api/v1/patients/{patient['id']}", headers=headers)
        assert patient_read.status_code == 200
        assert patient_read.json()["mrn"] == patient["mrn"]

        catalog_read = client.get(f"/api/v1/test-catalog/{catalog['id']}", headers=headers)
        assert catalog_read.status_code == 200
        assert catalog_read.json()["local_code"] == catalog["local_code"]

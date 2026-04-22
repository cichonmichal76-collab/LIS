from __future__ import annotations

from datetime import date
from uuid import uuid4

from sqlalchemy import select

from app.core.config import Settings
from app.core.security import hash_password
from app.db.models import PatientRecord, TestCatalogRecord, UserRecord
from app.db.session import DatabaseSessionManager


def main() -> None:
    settings = Settings.from_env()
    db = DatabaseSessionManager(settings.database_url)
    try:
        db.create_schema()
        session = db.session_factory()
        try:
            if session.scalar(select(UserRecord).where(UserRecord.username == "admin")) is None:
                session.add(
                    UserRecord(
                        id=str(uuid4()),
                        username="admin",
                        password_hash=hash_password("admin12345"),
                        display_name="Admin User",
                        role_code="admin",
                        active=True,
                    )
                )
            if session.scalar(select(PatientRecord).where(PatientRecord.mrn == "MRN-DEMO-001")) is None:
                session.add(
                    PatientRecord(
                        id=str(uuid4()),
                        mrn="MRN-DEMO-001",
                        given_name="Anna",
                        family_name="Nowak",
                        sex_code="F",
                        birth_date=date(1990, 1, 1),
                    )
                )
            if session.scalar(select(TestCatalogRecord).where(TestCatalogRecord.local_code == "GLU-DEMO")) is None:
                session.add(
                    TestCatalogRecord(
                        id=str(uuid4()),
                        local_code="GLU-DEMO",
                        display_name="Glucose demo",
                        kind="orderable",
                        loinc_num="2345-7",
                        specimen_type_code="serum",
                        default_ucum="mg/dL",
                        result_value_type="quantity",
                        active=True,
                    )
                )
            session.commit()
        finally:
            session.close()
    finally:
        db.dispose()
    print("Seeded demo users and master data.")


if __name__ == "__main__":
    main()

# `scripts/`

Ten katalog zawiera skrypty pomocnicze do uruchamiania i sprawdzania projektu.

## Co jest w srodku

- `migrate.py`
  Tworzy runtime schema aplikacji.
- `reset_db.py`
  Czysci baze SQLite albo PostgreSQL; opcjonalnie od razu odtwarza runtime schema.
- `wait_for_db.py`
  Czeka az baza odpowie, przydatne w Docker Compose i CI.
- `analyzer_runtime.py`
  Uruchamia background worker analizatorow poza request lifecycle API.
- `seed_demo_data.py`
  Laduje dane demonstracyjne.
- `export_openapi.py`
  Eksportuje aktualny kontrakt OpenAPI z aplikacji.
- `_smoke_support.py`
  Wspolne helpery dla smoke testow SQLite i PostgreSQL.
- `smoke_test.py`
  Podstawowy smoke test backendu LIS.
- `smoke_test_fhir.py`
  Smoke test fasady FHIR.
- `smoke_test_integration.py`
  Smoke test HL7 v2 i device gateway.
- `smoke_test_autoverification.py`
  Smoke test autoweryfikacji.
- `smoke_test_astm.py`
  Smoke test warstwy ASTM-style.
- `smoke_test_qc.py`
  Smoke test silnika QC i blokad gate dla observation/report.
- `smoke_test_transport.py`
  Smoke test warstwy transportowej analizatorow.
- `smoke_test_runtime.py`
  Smoke test background worker runtime analizatorow.
- `smoke_test_matrix.py`
  Uruchamia komplet smoke testow po kolei.

## Zastosowanie

To sa skrypty operacyjne dla dewelopera. Pozwalaja szybko sprawdzic, czy aplikacja nadal dziala po zmianach bez odpalania calego srodowiska produkcyjnego.

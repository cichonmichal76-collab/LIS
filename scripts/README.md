# `scripts/`

Ten katalog zawiera skrypty pomocnicze do uruchamiania i sprawdzania projektu.

## Co jest w środku

- `migrate.py`
  Tworzy runtime schema aplikacji.
- `seed_demo_data.py`
  Ładuje dane demonstracyjne.
- `export_openapi.py`
  Eksportuje aktualny kontrakt OpenAPI z aplikacji.
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

## Zastosowanie

To są skrypty operacyjne dla dewelopera. Pozwalają szybko sprawdzić, czy aplikacja nadal działa po zmianach bez odpalania pełnego środowiska produkcyjnego.

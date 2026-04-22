# `tests/`

Ten katalog zawiera testy automatyczne projektu.

## Co jest w środku

- `support.py`
  Wspólne helpery testowe.
- `test_auth_master_data.py`
  Testy auth i master data.
- `test_workflows.py`
  Podstawowe workflow LIS.
- `test_observations_reports.py`
  Wyniki i raporty.
- `test_fhir_facade.py`
  Fasada FHIR.
- `test_integrations.py`
  HL7 v2 i device gateway.
- `test_autoverification.py`
  Autoweryfikacja.
- `test_astm_integration.py`
  Integracje ASTM-style.

## Cel

Testy mają potwierdzać działanie najważniejszych slice'ów domenowych oraz regresje w integracjach i workflow.

## Jak czytać

Najlepiej zaczynać od:

1. `test_workflows.py`
2. `test_observations_reports.py`
3. `test_integrations.py`
4. `test_fhir_facade.py`

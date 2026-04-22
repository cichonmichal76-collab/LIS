# Struktura Repozytorium

Ten dokument opisuje **aktualną, rzeczywistą strukturę repo** dla startera LIS v6 oraz krótko pokazuje, jak ten układ może ewoluować później.

## Aktualna Struktura Repo

```text
LIS/
|-- app/
|   |-- api/
|   |-- core/
|   |-- db/
|   |-- schemas/
|   |-- services/
|   `-- main.py
|-- data/
|-- db/
|   |-- migrations/
|   |   |-- postgres/
|   |   `-- sqlite/
|   |-- lis.sqlite3
|   `-- schema.sql
|-- docs/
|-- openapi/
|-- scripts/
|-- tests/
|-- .dockerignore
|-- .gitignore
|-- Dockerfile
|-- docker-compose.yml
|-- pyproject.toml
`-- README.md
```

## Opisy Katalogów Głównych

- `app/`
  Główny kod aplikacji backendowej. Tu znajduje się API, logika domenowa, konfiguracja oraz modele persistence.
- `data/`
  Katalog roboczy na lokalne artefakty developerskie, głównie bazy SQLite tworzone przez smoke testy.
- `db/`
  Katalog bazy danych. Trzyma kanoniczny schemat SQL, migracje oraz lokalną bazę developerską SQLite.
- `docs/`
  Dokumentacja architektury, integracji, workflow i walidacji projektu.
- `openapi/`
  Wygenerowane i przechowywane kontrakty API.
- `scripts/`
  Skrypty pomocnicze do migracji, seedowania danych, eksportu OpenAPI i smoke testów.
- `tests/`
  Testy automatyczne repo: workflow, integracje, FHIR, autoweryfikacja i ASTM.

## Opisy Plików Głównych

- `README.md`
  Główny opis projektu, szybki start i aktualny zakres funkcjonalny.
- `pyproject.toml`
  Konfiguracja pakietu Python, zależności i narzędzi developerskich.
- `Dockerfile`
  Obraz aplikacji backendowej do uruchamiania w kontenerze.
- `docker-compose.yml`
  Lokalny stack uruchomieniowy dla API i PostgreSQL.
- `.gitignore`
  Reguły ignorowania plików lokalnych, cache i artefaktów tymczasowych.
- `.dockerignore`
  Reguły pomijania plików przy budowie obrazu Dockera.

## Katalog `app/`

```text
app/
|-- api/
|-- core/
|-- db/
|-- schemas/
|-- services/
`-- main.py
```

### `app/main.py`

Punkt wejścia aplikacji FastAPI. Składa wszystkie routery, ustawia lifecycle, podpina bazę i publikuje root endpoint.

### `app/api/`

Warstwa HTTP. Każdy plik reprezentuje router albo pomocniczy moduł dla endpointów.

```text
app/api/
|-- audit.py
|-- auth.py
|-- autoverification.py
|-- catalog.py
|-- deps.py
|-- devices.py
|-- fhir.py
|-- health.py
|-- helpers.py
|-- integrations.py
|-- observations.py
|-- orders.py
|-- patients.py
|-- reports.py
|-- specimens.py
`-- tasks.py
```

- `auth.py`
  Endpointy logowania, bootstrap admina i odczytu bieżącego użytkownika.
- `patients.py`
  Operacje na pacjentach.
- `catalog.py`
  Operacje na katalogu badań.
- `orders.py`
  Endpointy zleceń i pozycji zleceń.
- `specimens.py`
  Akcesjonowanie oraz lifecycle próbki.
- `tasks.py`
  Kolejki robocze i przejścia stanów tasków.
- `observations.py`
  Wyniki laboratoryjne, manual entry, verify i korekty.
- `reports.py`
  Generowanie, autoryzacja, wersjonowanie i PDF raportów.
- `devices.py`
  Rejestr urządzeń i mapowania testów wejściowych.
- `integrations.py`
  Integracje HL7 v2, device gateway, ASTM oraz logi interfejsowe.
- `autoverification.py`
  API reguł autoweryfikacji, evaluate, apply i historia uruchomień.
- `audit.py`
  Odczyt audytu i provenance przez REST.
- `fhir.py`
  Fasada FHIR R4 do read/search i `CapabilityStatement`.
- `health.py`
  Prosty endpoint zdrowia aplikacji.
- `deps.py`
  Zależności FastAPI, głównie auth i sesja DB.
- `helpers.py`
  Wspólne funkcje pomocnicze dla routerów.

### `app/core/`

Wspólna konfiguracja aplikacji i bezpieczeństwo.

```text
app/core/
|-- config.py
`-- security.py
```

- `config.py`
  Nazwa aplikacji, wersja i ustawienia środowiskowe.
- `security.py`
  JWT, hashowanie haseł i pomocnicze elementy bezpieczeństwa.

### `app/db/`

Warstwa persistence.

```text
app/db/
|-- base.py
|-- models.py
`-- session.py
```

- `base.py`
  Bazowa klasa modeli SQLAlchemy.
- `models.py`
  Runtime modele bazy dla SQLite/PostgreSQL path aplikacji.
- `session.py`
  Tworzenie engine, session factory i bootstrap schematu runtime.

### `app/schemas/`

Modele wejścia i wyjścia API. To warstwa kontraktów Pydantic dla REST.

```text
app/schemas/
|-- audit.py
|-- auth.py
|-- autoverification.py
|-- catalog.py
|-- common.py
|-- devices.py
|-- integrations.py
|-- observations.py
|-- orders.py
|-- patients.py
|-- reports.py
|-- specimens.py
`-- tasks.py
```

- Każdy plik opisuje requesty, response’y i typy dla odpowiadającego mu obszaru domenowego.
- `common.py` trzyma wspólne typy wykorzystywane przez kilka modułów.

### `app/services/`

Właściwa logika biznesowa systemu.

```text
app/services/
|-- astm.py
|-- audit.py
|-- auth.py
|-- autoverification.py
|-- catalog.py
|-- devices.py
|-- fhir.py
|-- hl7v2.py
|-- integrations.py
|-- observations.py
|-- orders.py
|-- patients.py
|-- provenance.py
|-- reports.py
|-- specimens.py
`-- tasks.py
```

- `orders.py`, `specimens.py`, `tasks.py`, `observations.py`, `reports.py`
  Główna logika LIS dla workflow laboratoryjnego.
- `auth.py`
  Użytkownicy, logowanie i tokeny.
- `catalog.py`, `patients.py`, `devices.py`
  Master data.
- `audit.py`, `provenance.py`
  Append-only audit trail i ślad pochodzenia danych.
- `fhir.py`
  Mapowanie z modelu LIS na zasoby FHIR R4.
- `hl7v2.py`
  Parsery i buildery HL7 v2.
- `integrations.py`
  Orkiestracja importów/eksportów, worklist, device gateway i połączenie z logiką domenową.
- `autoverification.py`
  Silnik reguł autoweryfikacji i przejść `auto-finalized` albo `manual-review`.
- `astm.py`
  Mały parser/builder warstwy ASTM-style.

## Katalog `db/`

```text
db/
|-- migrations/
|   |-- postgres/
|   |   |-- 0001_init.sql
|   |   `-- 002_autoverification_astm.sql
|   |-- sqlite/
|   |   |-- 0001_init.sql
|   |   `-- 002_autoverification_astm.sql
|   `-- 0001_lis_core.sql
|-- lis.sqlite3
`-- schema.sql
```

- `schema.sql`
  Kanoniczny target schema dla szerszej architektury LIS.
- `migrations/0001_lis_core.sql`
  Wczesna migracja rdzenia projektu.
- `migrations/sqlite/`
  Checked-in migracje dla ścieżki SQLite.
- `migrations/postgres/`
  Checked-in migracje dla ścieżki PostgreSQL.
- `lis.sqlite3`
  Lokalna baza developerska.

## Katalog `openapi/`

```text
openapi/
|-- lis-internal-v1.yaml
`-- lis-target-v1.yaml
```

- `lis-internal-v1.yaml`
  Aktualny kontrakt tego, co jest już wdrożone i działa.
- `lis-target-v1.yaml`
  Szerszy kontrakt docelowy, używany jako punkt odniesienia architektonicznego.

## Katalog `scripts/`

```text
scripts/
|-- export_openapi.py
|-- migrate.py
|-- seed_demo_data.py
|-- smoke_test.py
|-- smoke_test_astm.py
|-- smoke_test_autoverification.py
|-- smoke_test_fhir.py
`-- smoke_test_integration.py
```

- `migrate.py`
  Tworzy runtime schema aplikacji.
- `seed_demo_data.py`
  Ładuje dane demonstracyjne.
- `export_openapi.py`
  Eksportuje aktualny kontrakt OpenAPI z aplikacji.
- `smoke_test.py`
  Podstawowy end-to-end dla core LIS.
- `smoke_test_fhir.py`
  Smoke test dla fasady FHIR.
- `smoke_test_integration.py`
  Smoke test dla HL7 v2 i device gateway.
- `smoke_test_autoverification.py`
  Smoke test dla autoweryfikacji.
- `smoke_test_astm.py`
  Smoke test dla ASTM-style layer.

## Katalog `tests/`

```text
tests/
|-- support.py
|-- test_astm_integration.py
|-- test_auth_master_data.py
|-- test_autoverification.py
|-- test_fhir_facade.py
|-- test_integrations.py
|-- test_observations_reports.py
`-- test_workflows.py
```

- `support.py`
  Wspólne helpery testowe.
- `test_auth_master_data.py`
  Auth, użytkownicy i master data.
- `test_workflows.py`
  Podstawowy workflow LIS.
- `test_observations_reports.py`
  Wyniki i raporty.
- `test_fhir_facade.py`
  FHIR facade.
- `test_integrations.py`
  Device gateway i HL7 v2.
- `test_autoverification.py`
  Reguły autoweryfikacji.
- `test_astm_integration.py`
  Worklisty i import ASTM.

## Katalog `docs/`

```text
docs/
|-- alignment.md
|-- architecture.md
|-- astm-driver-layer.md
|-- autoverification-engine.md
|-- backlog.md
|-- device-gateway.md
|-- fhir-facade.md
|-- fhir-mapping.md
|-- hl7-v2-adapter.md
|-- repo-structure.md
|-- validation.md
`-- workflow.md
```

- `architecture.md`
  Ogólna architektura systemu.
- `workflow.md`
  Główny przepływ laboratoryjny.
- `fhir-facade.md`
  Założenia i granice fasady FHIR.
- `hl7-v2-adapter.md`
  Adapter HL7 v2.
- `device-gateway.md`
  Device gateway i integracje analizatorowe.
- `autoverification-engine.md`
  Silnik autoweryfikacji.
- `astm-driver-layer.md`
  Warstwa ASTM-style.
- `fhir-mapping.md`
  Mapowanie modelu LIS na FHIR.
- `validation.md`
  Wyniki walidacji lokalnej.
- `alignment.md`
  Różnice między target design a runtime.
- `backlog.md`
  Kierunki dalszej rozbudowy.
- `repo-structure.md`
  Ten dokument.

## Katalogi Lokalne, Które Nie Są Częścią Domeny

- `.venv/`
  Lokalny virtualenv Python.
- `.pytest_cache/`
  Cache pytest.
- `.ruff_cache/`
  Cache lintera Ruff.
- `lis_core.egg-info/`
  Artefakty pakietowania setuptools.

Te katalogi są pomocnicze i nie opisują logiki LIS.

## Jak Czytać Ten Repo

Najprostsza ścieżka wejścia dla nowej osoby:

1. Zacząć od `README.md`.
2. Potem przeczytać `docs/architecture.md`, `docs/workflow.md` i ten plik.
3. Następnie wejść do `app/main.py`, `app/api/`, `app/services/` i `app/db/models.py`.
4. Na końcu sprawdzić `scripts/smoke_test*.py` i `tests/`, bo pokazują, co naprawdę działa end-to-end.

## Kierunek Dalszego Wzrostu

Repo nadal jest **modularnym monolitem**. To jest zamierzone.

Jeżeli system urośnie, naturalny kierunek rozdziału będzie taki:

- osobny `fhir-facade`
- osobny `device-gateway`
- osobny renderer raportów
- osobny worker dla zadań asynchronicznych

Na obecnym etapie wszystko jest jednak trzymane razem celowo, żeby nie rozpraszać złożoności domenowej na zbyt wiele deployowalnych komponentów.

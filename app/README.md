# `app/`

Ten katalog zawiera właściwy kod backendu LIS.

## Co jest w środku

- `main.py`
  Punkt wejścia aplikacji FastAPI. Składa routery, uruchamia lifecycle i podpina bazę.
- `api/`
  Warstwa HTTP. Tu są endpointy REST i FHIR.
- `core/`
  Konfiguracja aplikacji, wersja, ustawienia środowiskowe i bezpieczeństwo.
- `db/`
  Runtime persistence: modele SQLAlchemy, baza i sesje.
- `schemas/`
  Modele Pydantic dla requestów i response'ów.
- `services/`
  Logika biznesowa LIS: workflow, integracje, autoweryfikacja, FHIR mapping, audit i provenance.

## Jak czytać ten katalog

Najprostsza ścieżka:

1. `main.py`
2. `api/`
3. `services/`
4. `db/models.py`
5. `schemas/`

## Najważniejsza zasada

`api/` powinno być cienkie. Właściwa logika powinna trafiać do `services/`, a nie zostawać w routerach.

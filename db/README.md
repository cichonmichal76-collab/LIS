# `db/`

Ten katalog trzyma schemat i migracje bazy danych dla projektu LIS.

## Co jest w środku

- `schema.sql`
  Kanoniczny, szerszy schemat docelowy systemu.
- `migrations/0001_lis_core.sql`
  Wczesna migracja rdzenia projektu.
- `migrations/sqlite/`
  Checked-in migracje dla ścieżki SQLite.
- `migrations/postgres/`
  Checked-in migracje dla ścieżki PostgreSQL.
- `lis.sqlite3`
  Lokalna baza developerska używana przez runtime aplikacji.

## Jak to czytać

- `schema.sql` pokazuje, dokąd architektonicznie zmierza system.
- katalogi `migrations/sqlite` i `migrations/postgres` pokazują praktyczne kroki migracyjne, które są utrzymywane razem z kodem.

## Uwaga

Na dziś lokalnie potwierdzona end-to-end jest ścieżka SQLite. PostgreSQL jest przygotowany kodowo i migracyjnie, ale nie został jeszcze domknięty pełnym E2E w tym środowisku.

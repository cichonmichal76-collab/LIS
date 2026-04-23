# Runtime Bootstrap

Ten dokument opisuje v13, czyli przejscie na jawny bootstrap operacyjnego schematu runtime.

## Po co ten etap

Do v12 repo mialo dwa swiaty:

- modele ORM w `app/db/models.py`
- kanoniczne migracje target design w `db/migrations/sqlite/*.sql` i `db/migrations/postgres/*.sql`

To bylo wartosciowe projektowo, ale nie bylo jeszcze jednym, jasnym mechanizmem bootstrapu
aktualnego schematu operacyjnego aplikacji.

V13 dodaje brakujace ogniwo:

- checked-in runtime bootstrap SQL pod obecne tabele `_runtime`
- jawne tryby bootstrapu
- CI, ktore pilnuje zgodnosci snapshotu z modelami

## Nowe artefakty

- [db/runtime_bootstrap/sqlite.sql](C:/Users/cicho/OneDrive/Pulpit/LIS/db/runtime_bootstrap/sqlite.sql)
- [db/runtime_bootstrap/postgres.sql](C:/Users/cicho/OneDrive/Pulpit/LIS/db/runtime_bootstrap/postgres.sql)
- [scripts/export_runtime_bootstrap.py](C:/Users/cicho/OneDrive/Pulpit/LIS/scripts/export_runtime_bootstrap.py)
- [scripts/validate_sql_artifacts.py](C:/Users/cicho/OneDrive/Pulpit/LIS/scripts/validate_sql_artifacts.py)

Snapshoty runtime sa generowane z:

- [app/db/models.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/db/models.py)

## Tryby bootstrapu

Konfiguracja odbywa sie przez:

- `LIS_AUTO_CREATE_SCHEMA`
- `LIS_SCHEMA_BOOTSTRAP_MODE`

Obslugiwane tryby:

- `runtime-sql`
  Preferowany tryb v13. Aplikacja i `scripts/migrate.py` uzywaja checked-in snapshotu runtime SQL.
- `metadata`
  Fallback developerski. Bootstrap odbywa sie przez `Base.metadata.create_all(...)`.
- `none`
  Aplikacja nie bootstrappuje schematu sama.

## Jak to dziala

### App startup

Przy `LIS_AUTO_CREATE_SCHEMA=true` aplikacja wywoluje bootstrap zgodnie z `LIS_SCHEMA_BOOTSTRAP_MODE`.

Glowny kod siedzi w:

- [app/main.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/main.py)
- [app/db/session.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/db/session.py)
- [app/db/runtime.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/db/runtime.py)

### Migrate script

[scripts/migrate.py](C:/Users/cicho/OneDrive/Pulpit/LIS/scripts/migrate.py) przyjmuje teraz:

- `--database-url`
- `--mode`

Domyslnie bierze wartosci z env.

### Snapshot check

`python scripts/export_runtime_bootstrap.py --check`

sprawdza, czy checked-in pliki SQL zgadzaja sie z aktualnymi modelami ORM.

To jest wykonywane tez w CI.

## Relacja do kanonicznych migracji

To nadal sa dwa osobne poziomy:

- `db/runtime_bootstrap/*.sql`
  operacyjny bootstrap aktualnego backendu
- `db/migrations/sqlite/*.sql` i `db/migrations/postgres/*.sql`
  szerszy target design i artefakty projektowe

V13 nie usuwa kanonicznych migracji. Uporzadkowuje po prostu to,
z czego backend ma sie rzeczywiscie startowac.

## Granica etapu

To nadal nie jest pelny framework migracyjny z historią rewizji runtime.

Brakuje jeszcze:

- sekwencyjnych runtime migrations zamiast snapshot bootstrapu,
- twardego diff checku runtime schema vs live database,
- bardziej formalnego upgrade path dla starszych baz bez resetu,
- CI rerun na Docker Compose w tym lokalnym srodowisku.

Najuczciwiej: v13 daje checked-in runtime SQL jako jawne zrodlo prawdy dla bootstrapu operacyjnego,
ale jeszcze nie jest pelnym systemem rewizji schematu runtime.

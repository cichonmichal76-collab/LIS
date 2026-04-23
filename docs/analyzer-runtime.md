# Analyzer Runtime

Ten dokument opisuje v9-v12, czyli osobny runtime analizatorow dzialajacy poza request lifecycle API
oraz jego pozniejsze utwardzenie operacyjne.

## Po co ten etap

Po v8 repo mialo juz:

- sesje transportowe,
- framing ASTM-style,
- `ENQ`, `ACK`, `NAK`, `EOT`,
- retry,
- dispatch do importu ASTM.

Brakowalo jednak procesu, ktory:

- trzyma polaczenie z analizatorem,
- czyta i zapisuje dane poza pojedynczym requestem HTTP,
- wykonuje transport w tle.

To wlasnie robi analyzer runtime.

## Co dochodzi w v9

### Worker runtime

Worker uruchamiany przez [scripts/analyzer_runtime.py](C:/Users/cicho/OneDrive/Pulpit/LIS/scripts/analyzer_runtime.py)
wykonuje cykle pracy:

1. wybiera aktywne profile transportowe,
2. zapewnia aktywna sesje dla profilu,
3. otwiera odpowiedni konektor,
4. czyta inbound transport items,
5. obsluguje timeouty oczekujacych ACK,
6. wysyla kolejne outbound items.

Glowna logika jest w [app/services/analyzer_runtime.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/services/analyzer_runtime.py).

### Konektory

Runtime ma trzy tryby polaczen:

- `mock`
- `tcp-client`
- `serial`

`mock` sluzy do testow i smoke flow.

`tcp-client` korzysta ze standardowej biblioteki `socket` i czyta:

- pojedyncze control chars,
- ramki zakonczone `CRLF`.

`serial` jest przygotowany architektonicznie, ale wymaga `pyserial`.

### Konfiguracja runtime w profilu transportowym

Profil transportowy przechowuje teraz nie tylko framing i retry, ale tez konfiguracje endpointu:

- `connection_mode`
- `tcp_host`
- `tcp_port`
- `serial_port`
- `serial_baudrate`
- `poll_interval_seconds`
- `read_timeout_seconds`
- `write_timeout_seconds`
- `auto_dispatch_astm`
- `auto_verify`

Dzieki temu worker moze dzialac na podstawie danych zapisanych w bazie, a nie tylko na twardo zakodowanych parametrach.

## Co dochodzi w v12

V12 utwardza runtime bez wymagania fizycznego analizatora.

Dochodzi:

- lease ownership dla sesji transportowych,
- heartbeat i lease expiry,
- retry backoff po bledach runtime,
- reset konektora po bledzie,
- runtime overview API pod `/api/v1/analyzer-transport/runtime/overview`,
- dodatkowe checked-in migracje dla lease/backoff.

To pozwala bezpieczniej uruchamiac wiecej niz jeden worker i odroznic:

- sesje aktualnie obslugiwane,
- sesje z wygaslym lease,
- sesje czekajace w backoff po bledzie.

## Jak worker dziala

### Inbound

Worker odczytuje z konektora dane i klasyfikuje je jako:

- control code
- frame

Potem przekazuje je do istniejacej warstwy transportowej:

- control -> `receive_transport_control`
- frame -> `receive_transport_frame`

Jesli backend powinien odpowiedziec:

- `ACK`
- `NAK`

worker od razu odsyla payload przez konektor.

Jesli finalna wiadomosc ma `auto_dispatch_astm=true`, runtime automatycznie dispatchuje ja
do istniejacego importu ASTM i opcjonalnie uruchamia autoweryfikacje.

### Outbound

Worker pobiera kolejny element do wyslania przez:

- `next_outbound_transport_item`

Po wyslaniu:

- czeka na inbound odpowiedz,
- przekazuje `ACK` lub `NAK` do warstwy transportowej,
- albo po przekroczeniu deadline wywoluje timeout.

### Lease i backoff

Kazdy cykl worker:

1. probuje przejac lease dla sesji,
2. pomija sesje z aktywnym lease innego workera,
3. pomija sesje, ktore sa jeszcze w `next_retry_at`,
4. odswieza heartbeat dla sesji, ktora sam posiada,
5. po sukcesie zeruje `failure_count` i czyści `next_retry_at`,
6. po bledzie ustawia `session_status=error`, inkrementuje `failure_count`
   i wylicza rosnacy backoff.

Przy zamknieciu workera jego lease sa zwalniane.

### Runtime overview

Endpoint `/api/v1/analyzer-transport/runtime/overview` pokazuje aktualny stan runtime:

- liczbe profili,
- liczbe sesji,
- liczbe aktywnych lease,
- liczbe wygaslych lease,
- liczbe sesji w backoff,
- liczbe sesji w stanie `error`.

## Testy i smoke

Ten etap ma osobne potwierdzenie dzialania:

- [tests/test_analyzer_runtime.py](C:/Users/cicho/OneDrive/Pulpit/LIS/tests/test_analyzer_runtime.py)
- [scripts/smoke_test_runtime.py](C:/Users/cicho/OneDrive/Pulpit/LIS/scripts/smoke_test_runtime.py)

Testy obejmuja:

- outbound `ENQ -> FRAME -> EOT`
- inbound `ENQ + ASTM frame + EOT`
- dispatch do importu ASTM
- finalizacje observation przez autoweryfikacje
- respektowanie aktywnego lease i przejecie lease wygaslego
- backoff po bledzie runtime
- runtime overview z licznikami lease/backoff/error

## Docker Compose

W [docker-compose.yml](C:/Users/cicho/OneDrive/Pulpit/LIS/docker-compose.yml) jest osobny serwis:

- `analyzer-runtime`

Uruchamia on:

1. `wait_for_db.py`
2. `migrate.py`
3. `analyzer_runtime.py`

To daje gotowy punkt startowy pod lokalne albo kontenerowe uruchamianie workera.

## Granica tego etapu

To nadal nie jest pelny, produkcyjny driver analizatora.

Brakuje jeszcze:

- lepszej rekoneksji i recovery po rozlaczeniach,
- bardziej rozbudowanego replay/dead-letter flow,
- potwierdzonej sciezki `pyserial`,
- bogatszej obslugi framingu i site-specific wariantow protokolow,
- eksportu metrics i stalego monitoringu runtime.

Najuczciwiej: v12 daje dzialajacy background worker z leasingiem, backoff i overview API,
ale nie jest jeszcze finalnym, produkcyjnym middleware analyzerowym.

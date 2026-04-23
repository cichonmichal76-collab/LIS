# Analyzer Runtime

Ten dokument opisuje v9, czyli osobny runtime analizatorow dzialajacy poza request lifecycle API.

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

## Testy i smoke

Ten etap ma osobne potwierdzenie dzialania:

- [tests/test_analyzer_runtime.py](C:/Users/cicho/OneDrive/Pulpit/LIS/tests/test_analyzer_runtime.py)
- [scripts/smoke_test_runtime.py](C:/Users/cicho/OneDrive/Pulpit/LIS/scripts/smoke_test_runtime.py)

Testy obejmuja:

- outbound `ENQ -> FRAME -> EOT`
- inbound `ENQ + ASTM frame + EOT`
- dispatch do importu ASTM
- finalizacje observation przez autoweryfikacje

## Docker Compose

W [docker-compose.yml](C:/Users/cicho/OneDrive/Pulpit/LIS/docker-compose.yml) jest teraz osobny serwis:

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
- bardziej rozbudowanego scheduler/lease modelu dla wielu workerow,
- potwierdzonej sciezki `pyserial`,
- bogatszej obslugi framingu i site-specific wariantow protokolow,
- monitoringu i metrics dla stalego runtime.

Najuczciwiej: v9 daje dzialajacy background worker i abstrakcje fizycznego I/O,
ale nie jest jeszcze finalnym, produkcyjnym middleware analyzerowym.

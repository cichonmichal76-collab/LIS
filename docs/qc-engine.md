# QC Engine

Ten dokument opisuje v10, czyli pierwszy dzialajacy silnik kontroli jakosci w backendzie LIS.

## Po co ten etap

Po v9 repo mialo juz:

- rdzen wynikowy,
- autoweryfikacje,
- raporty,
- HL7/ASTM,
- transport i runtime analizatorow.

Brakowalo jednak bramki jakosci, ktora odpowiada na pytanie:

- czy dla danego testu i urzadzenia ostatni QC pozwala w ogole wypuscic wynik dalej.

To wlasnie robi QC engine.

## Co dochodzi w v10

### Master data QC

Doszly nowe byty:

- `qc_material`
- `qc_lot`
- `qc_rule`
- `qc_run`
- `qc_result`

W runtime odpowiadaja im modele w [app/db/models.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/db/models.py).

### Reguly i ocena runu

Silnik QC pozwala ocenic run na podstawie:

- zakresu lotu,
- `westgard_12s`,
- `westgard_13s`,
- `westgard_22s`,
- `westgard_r4s`,
- `westgard_41s`.

Glowna logika siedzi w [app/services/qc.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/services/qc.py).

Wynik oceny moze byc:

- `pass`
- `warning`
- `fail`

Status calego runu moze byc:

- `open`
- `passed`
- `warning`
- `failed`

### Gate dla observation i report

Najwazniejsza rzecz w tym etapie to QC gate.

Jesli dla testu i zakresu urzadzenia jest aktywny QC:

- backend szuka ostatniego ocenionego `qc_result`,
- jezeli go nie ma, wynik nie przechodzi gate,
- jezeli ostatni QC ma `fail`, wynik nie przechodzi gate,
- `pass` i `warning` przepuszczaja gate.

QC gate zostal wpiety w dwa miejsca:

- autoweryfikacja observation
- autoryzacja raportu

To oznacza, ze nawet jesli observation istnieje, to bez zaliczonego QC nie powinna przejsc
automatycznie do final ani pozwolic na finalne podpisanie raportu.

## API

Router QC jest w [app/api/qc.py](C:/Users/cicho/OneDrive/Pulpit/LIS/app/api/qc.py).

Najwazniejsze endpointy:

- `POST /api/v1/qc/materials`
- `GET /api/v1/qc/materials`
- `POST /api/v1/qc/lots`
- `GET /api/v1/qc/lots`
- `POST /api/v1/qc/rules`
- `GET /api/v1/qc/rules`
- `POST /api/v1/qc/runs`
- `GET /api/v1/qc/runs`
- `GET /api/v1/qc/runs/{id}`
- `POST /api/v1/qc/runs/{id}/results`
- `GET /api/v1/qc/runs/{id}/results`
- `POST /api/v1/qc/runs/{id}/evaluate`
- `GET /api/v1/qc/observations/{id}/gate`

## Testy i smoke

Ten etap ma osobne potwierdzenie dzialania:

- [tests/test_qc_engine.py](C:/Users/cicho/OneDrive/Pulpit/LIS/tests/test_qc_engine.py)
- [scripts/smoke_test_qc.py](C:/Users/cicho/OneDrive/Pulpit/LIS/scripts/smoke_test_qc.py)

Testy pokrywaja:

- warning i fail dla regul Westgarda,
- blokade autoweryfikacji przy braku ocenionego QC,
- blokade autoryzacji raportu do momentu uzyskania poprawnego QC.

## Granica tego etapu

To nadal nie jest pelny komercyjny QC middleware.

Brakuje jeszcze:

- wielopoziomowych materialow i poziomow kontroli,
- lotow reagentow i pelnego powiazania reagent-QC-device,
- bogatszych regul Westgarda i trendow wielopoziomowych,
- harmonogramow QC i polityk wymaganych przed pierwszym patient run,
- blokad workflow zaleznych od laboratorium, sekcji i analizatora.

Najuczciwiej: v10 daje dzialajacy, praktyczny QC gate i starter rule engine,
ale nie jest jeszcze pelnym systemem kontroli jakosci dla produkcyjnego laboratorium.

# Analyzer Transport

Ten dokument opisuje warstwe transportowa analizatorow dodana w etapie v8.

## Cel

Warstwa transportowa domyka lukę pomiedzy:

- logicznym `device gateway`,
- istniejacym importem ASTM results,
- a realnym protokolem sesji i ramek typu ASTM-style.

To nie jest jeszcze fizyczny driver TCP lub RS-232. To jest backendowy engine
sesji, kolejek, ramek i odpowiedzi `ACK`/`NAK`.

## Co dochodzi

### Profile transportowe

Tabela `analyzer_transport_profile` przechowuje ustawienia transportu per urzadzenie:

- `protocol`
- `framing_mode`
- `frame_payload_size`
- `ack_timeout_seconds`
- `max_retries`
- `active`

Profil jest przypisany do urzadzenia i pozwala utrzymac rozne ustawienia dla roznych analizatorow.

### Sesje transportowe

Tabela `analyzer_transport_session` reprezentuje aktywna sesje wymiany ramek.

Glowne stany:

- `idle`
- `sending`
- `receiving`
- `awaiting_ack`
- `closed`
- `error`

Sesja przechowuje tez:

- aktualna wiadomosc outbound,
- aktualna wiadomosc inbound,
- oczekiwany numer kolejnej ramki inbound,
- ostatni blad i znacznik aktywnosci.

### Wiadomosci transportowe

Tabela `analyzer_transport_message` przechowuje logical payload i stan transportowy.

Kierunki:

- `inbound`
- `outbound`

Stany:

- `queued`
- `ready`
- `awaiting_ack`
- `resend`
- `completed`
- `failed`
- `receiving`
- `received`
- `dispatched`

Wiadomosc przechowuje:

- payload logiczny,
- payload zlozony po odbiorze ramek,
- liste ramek,
- indeks kolejnej ramki,
- ostatnio wyslany typ elementu (`ENQ`, `FRAME`, `EOT`),
- retry count,
- deadline na ACK,
- informacje o dispatchu do importu ASTM.

### Log ramek

Tabela `analyzer_transport_frame_log` przechowuje wszystkie zdarzenia transportowe:

- control events,
- data frames,
- checksum,
- final frame marker,
- `accepted`,
- `duplicate_flag`,
- `retry_no`,
- notatki diagnostyczne.

To jest glowny sladowy log zachowania transportu.

## ASTM-style framing

Warstwa transportowa obsluguje:

- `STX`
- `ETB`
- `ETX`
- `CRLF`
- checksum hex
- numeracje ramek `1..7` z zawijaniem

Outbound:

1. `ENQ`
2. kolejne ramki
3. `EOT`

Inbound:

1. `ENQ`
2. ramki danych
3. `EOT`

## ACK / NAK / timeout

Silnik obsluguje:

- `ACK`
- `NAK`
- timeout
- resend
- fail po przekroczeniu `max_retries`

Logika outbound wyglada tak:

1. `queued` wysyla `ENQ`
2. `ACK` po `ENQ` przechodzi do `ready`
3. `ready` wysyla kolejna ramke albo `EOT`
4. `ACK` po ramce przesuwa indeks
5. `NAK` lub timeout ustawia `resend`
6. po przekroczeniu limitu retry wiadomosc przechodzi do `failed`

## Duplicate detection

Inbound duplicate detection dziala na poziomie zaakceptowanej ramki w tej samej wiadomosci transportowej.

Jesli backend dostaje drugi raz identyczna, juz zaakceptowana ramke:

- oznacza ja jako duplikat,
- zapisuje to w `analyzer_transport_frame_log`,
- odpowiada `ACK`,
- nie sklada payloadu drugi raz.

## Dispatch do ASTM importu

Po zlozeniu finalnej wiadomosci inbound backend moze:

- dispatchowac ja recznie:
  - `POST /api/v1/analyzer-transport/messages/{message_id}/dispatch/astm`
- albo automatycznie:
  - `auto_dispatch_astm=true` przy `inbound/frame`

Dispatch spina te warstwe z istniejacym:

- importerem ASTM results,
- device mappings,
- observation creation,
- autoweryfikacja.

Po udanym dispatchu wiadomosc transportowa zapisuje:

- `dispatched_entity_type = raw_instrument_message`
- `dispatched_entity_id`

## Endpointy

- `POST /api/v1/analyzer-transport/profiles`
- `GET /api/v1/analyzer-transport/profiles`
- `POST /api/v1/analyzer-transport/sessions`
- `GET /api/v1/analyzer-transport/sessions`
- `GET /api/v1/analyzer-transport/sessions/{id}`
- `GET /api/v1/analyzer-transport/sessions/{id}/messages`
- `GET /api/v1/analyzer-transport/sessions/{id}/frames`
- `POST /api/v1/analyzer-transport/sessions/{id}/queue-outbound`
- `POST /api/v1/analyzer-transport/sessions/{id}/queue-astm-worklist`
- `POST /api/v1/analyzer-transport/sessions/{id}/outbound/next`
- `POST /api/v1/analyzer-transport/sessions/{id}/outbound/ack`
- `POST /api/v1/analyzer-transport/sessions/{id}/outbound/nak`
- `POST /api/v1/analyzer-transport/sessions/{id}/outbound/timeout`
- `POST /api/v1/analyzer-transport/sessions/{id}/inbound/control`
- `POST /api/v1/analyzer-transport/sessions/{id}/inbound/frame`
- `POST /api/v1/analyzer-transport/messages/{message_id}/dispatch/astm`

## Granica tego etapu

To nie jest jeszcze:

- osobny runtime utrzymujacy stale polaczenie z analizatorem,
- listener TCP,
- driver serial/RS-232,
- scheduler retry dzialajacy poza lifecycle pojedynczego requestu,
- vendor-specific low-level connector.

Czyli: logika transportowa jest juz backendowo gotowa, ale fizyczne I/O z analizatorem nadal wymaga kolejnego etapu.

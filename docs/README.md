# `docs/`

Tu znajduje sie dokumentacja projektowa i operacyjna repo.

## Najwazniejsze pliki

- `architecture.md`
  Architektura systemu.
- `workflow.md`
  Glowny workflow laboratoryjny.
- `repo-structure.md`
  Opis aktualnej struktury repo i katalogow.
- `dependency-tree.md`
  Drzewo zaleznosci modulow i warstw w aktualnym kodzie.
- `fhir-facade.md`
  Granice i sposob dzialania fasady FHIR.
- `hl7-v2-adapter.md`
  Adapter HL7 v2.
- `device-gateway.md`
  Device gateway i analiza komunikatow urzadzen.
- `autoverification-engine.md`
  Silnik autoweryfikacji.
- `qc-engine.md`
  Silnik kontroli jakosci i gate dla wynikow oraz raportow.
- `astm-driver-layer.md`
  Warstwa ASTM-style.
- `analyzer-transport.md`
  Warstwa transportowa analizatorow: sesje, ramki, ACK/NAK i retry.
- `analyzer-runtime.md`
  Background worker analizatorow i konektory mock/TCP/serial.
- `runtime-bootstrap.md`
  Jak dziala `runtime-sql`, snapshoty `db/runtime_bootstrap/*.sql` i tryby bootstrapu.
- `postgres-e2e.md`
  Jak uruchomic i sprawdzic pelny przebieg PostgreSQL E2E.
- `validation.md`
  Wyniki walidacji lokalnej i dockerowej.
- `alignment.md`
  Roznice miedzy target design a aktualnym runtime.
- `backlog.md`
  Kierunki dalszego rozwoju.

## Od czego zaczac

Jesli ktos wchodzi do projektu pierwszy raz, najlepiej czytac w tej kolejnosci:

1. `architecture.md`
2. `workflow.md`
3. `repo-structure.md`
4. dokumenty integracyjne i walidacyjne

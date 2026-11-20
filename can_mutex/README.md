# can_mutex: RTNL-Stalls in CAN_RAW, CAN_ISOTP und CAN_BCM, Folgepatches

Mainline-Patches, keine Stable-Backports.

## Patches 1 bis 8: Serie v7 (Fixes, für stable markiert)

"[PATCH v7 0/8] can: avoid RTNL stalls and fix CAN_ISOTP and netlink
issues", unverändert die mit b4 erzeugten Mails vom 20.11.2026 (lokale
Ausgabe, die Message-IDs der verschickten Serie können abweichen). Basis
ist net/main `4d67cf2fd235`. Die Serie ersetzt die acht Patches der v6 im
Pull-Request "pull-request: can 2026-11-17" von Marc Kleine-Budde.

| # | Patch | Autor | Fixes | gegenüber v6 |
|---|---|---|---|---|
| 1 | can: bcm: copy the CAN frames outside of lock_sock() | Oliver Hartkopp | `ffd980f976e7` | unverändert |
| 2 | can: bcm: do not remove the procfs entry in bcm_notify() | Oliver Hartkopp | `76fe372ccb81` | unverändert |
| 3 | can: raw: use a private mutex instead of lock_sock() | Oliver Hartkopp | `c18ce101f2e4` | unverändert |
| 4 | can: isotp: use a private mutex instead of lock_sock() | Oliver Hartkopp | `e057dd3fc20f` | unverändert |
| 5 | can: bcm: use a private mutex instead of lock_sock() | Oliver Hartkopp | `ffd980f976e7` | unverändert |
| 6 | can: isotp: always start the rx timeout in ISOTP_WAIT_DATA state | Oliver Hartkopp | `e057dd3fc20f` | Code und Text |
| 7 | can: isotp: reject socket options while a transfer is active | Oliver Hartkopp | `e057dd3fc20f` | Code und Text |
| 8 | can: netlink: fix static FD-NON-ISO mode validation | Zhu Ling | `6742ca18cb41` | nur Text |

- **Patch 1 bis 5** vermeiden RTNL-Stalls in CAN_BCM bzw. ersetzen
  `lock_sock()` durch den Mutex `conf_lock`, damit die generischen
  `SOL_SOCKET`-Optionen die Notifier nicht mehr unter RTNL aufhalten
  können. Patch 3 und 4 brauchen den Commit 43c973a0887d, Patch 5 braucht
  Patch 1 und 2.
- **Patch 6** startet den Empfangs-Timeout in `isotp_rcv_ff()` und
  `isotp_rcv_cf()`, bevor ein Flow Control gesendet wird. Neu in v7 (nach
  dem Sashiko-Review zu v6, `Reported-by`/`Closes`): `isotp_rcv_cf()`
  prüft die Länge eines Consecutive Frame als Erstes, vor der
  Zustandsprüfung, dem `force_rx_stmin`-Block und `hrtimer_cancel()`. Ein
  ungültiger CF wird so verworfen, ohne den laufenden Timeout anzuhalten
  oder den Zeitstempel für `CAN_ISOTP_FORCE_RXSTMIN` zu setzen. Ohne den
  Patch bleibt `so->rx.state` ohne Timer in `ISOTP_WAIT_DATA` stehen, und
  nach dem Entfernen des Devices lehnt `isotp_bind()` den Socket dauerhaft
  mit `-EAGAIN` ab.
- **Patch 7** prüft in `isotp_setsockopt_locked()` zusätzlich zu
  `so->bound`, dass Sende- und Empfangszustand idle sind, wie
  `isotp_bind()` es schon tut. Neu in v7: `isotp_sendmsg()` liest
  `CAN_ISOTP_EXTEND_ADDR` und `CAN_ISOTP_WAIT_TX_DONE` erst nach der
  Belegung der Übertragung und der erneuten Prüfung von `so->bound`.
  Patch 6 muss vorher kommen, sonst würde ein hängender Empfangszustand
  zusätzlich `setsockopt()` sperren.
- **Patch 8** ist Zhu Lings Fix, nach dem Sashiko-Review überarbeitet:
  Eine Anfrage, die einen statischen Modus ausschaltet, wird mit eigener
  Fehlermeldung abgelehnt. Neu in v7 ist ein Absatz, warum Kernel ohne
  6742ca18cb41 den Fix nicht brauchen (dort ändert ein verlorenes
  statisches Bit nur den gemeldeten Modus, nicht die Hardware). Zhu Ling
  bleibt Autor, die Überarbeitung ist als `[Hartkopp: ...]`-Notiz
  vermerkt. Zhus übrige Netlink-Patches aus dem Pull-Request wenden
  unverändert auf Patch 8 an.

Die bisher als Folgepatch vorbereitete CF-Längenprüfung ist in Patch 6
aufgegangen.

## Patches 9 und 10: Folgepatches für can-next (kein Fix, nicht stable)

| # | Patch |
|---|---|
| 9 | can: raw: read socket options under conf_lock in raw_getsockopt() |
| 10 | can: isotp: read socket options under conf_lock in isotp_getsockopt() |

Beide lesen die Optionswerte unter `conf_lock` in eine lokale Variable und
kopieren sie erst nach `mutex_unlock()` in den User-Space. Sie setzen auf
Patch 3 bzw. 4 auf und stellen den Struct-Kommentar auf "sockopts". Beide
sind neu geschrieben und noch nicht gegengelesen; der Signed-off-by des
Autors ist als Vorschlag eingetragen.

## Patch 11: memcg-Abrechnung für can-next (zurückgestellt)

| # | Patch |
|---|---|
| 11 | can: enable memcg accounting for user triggered allocations |

Der für v5 vorbereitete Stand ohne Abrechnung des isotp-RX-Puffers in
`isotp_rcv_ff()` (dort nur ein Kommentar), auf Patch 10 aufgesetzt. Der
Code ist gegenüber der vorbereiteten Fassung unverändert, die
Changelog-Notizen unter dem `---` sind übernommen. Der Patch wird erst
verschickt, wenn die Fixes in can-next angekommen sind; Changelog und
Links sind dann anzupassen.

## Prüfung

- Die Dateien 1 bis 11 wenden in dieser Reihenfolge per `git am` auf
  Mainline `067c5c24ce` an (den net-Tree `4d67cf2fd235` habe ich nicht;
  die betroffenen Dateien sind nach meinem Stand identisch).
- Code von Patch 1 bis 5 und 8 ist identisch mit der v6 (gleiche
  `git patch-id`). Patch 6 und 7 entsprechen genau der v6 plus den beiden
  besprochenen Änderungen.
- `net/can/` und `drivers/net/can/dev/` übersetzen nach jedem der Patches
  1 bis 11 fehler- und warnungsfrei (gcc 13.3, `W=1`, mit
  `CONFIG_PROVE_LOCKING`, `CONFIG_DEBUG_MUTEXES` und `CONFIG_PROC_FS`).
  Kein vollständiger Kernel-Build.
- checkpatch meldet nichts außer den bei mir unbekannten Commit-IDs.
- Laufzeittest der v7 (20.11.2026, Test-Suite `can-lock-tests-mutex-v5`,
  short, lockdep und KASAN): auf `7.4.0-rc3-net-locktest-00448-gb4092438c4d1`
  bestehen alle 14 Tests, `debug_locks` danach 1. `isotp_state_test` hat
  zwei neue Fälle für ungültige Consecutive Frames (CAN CC zu kurz, CAN FD
  zu lang):

  | Kernel | Fall 1 | Fall 2 bis 4 | Fall 5 und 6 |
  |---|---|---|---|
  | ohne Patch 6 und 7 (`...-00141-g9dac799e47f8`) | FAIL | FAIL | FAIL |
  | v6 (`...-00143-gab966e98efcf`) | PASS | PASS | FAIL |
  | v7 (`...-net-locktest-00448-gb4092438c4d1`) | PASS | PASS | PASS |

- Patch 8 ist nur übersetzt, nicht auf M_CAN- oder pcan_usb_fd-Hardware
  getestet.
- Patch 9 bis 11 sind nur übersetzt. Als Funktionstest für 9 und 10 bietet
  sich `sockopt_test` aus der Test-Suite an; die memcg-Abrechnung in
  Patch 11 ist ungetestet.

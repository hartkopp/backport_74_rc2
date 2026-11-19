# can_mutex: RTNL-Stalls in CAN_RAW, CAN_ISOTP und CAN_BCM, Folgepatches

Mainline-Patches, keine Stable-Backports.

## Patches 1 bis 8: Serie v6 (Fixes, für stable markiert)

"[PATCH v6 0/8] can: avoid RTNL stalls and fix CAN_ISOTP and netlink
issues", unverändert die mit b4 erzeugten Mails vom 17.11.2026 (lokale
Ausgabe, die Message-IDs der verschickten Serie können abweichen). Die
Serie ersetzt im Pull-Request "pull-request: can 2026-11-15" von Marc
Kleine-Budde die fünf Patches der v5 und Zhu Lings Patch 3/9.

| # | Patch | Autor | Fixes |
|---|---|---|---|
| 1 | can: bcm: copy the CAN frames outside of lock_sock() | Oliver Hartkopp | `ffd980f976e7` |
| 2 | can: bcm: do not remove the procfs entry in bcm_notify() | Oliver Hartkopp | `76fe372ccb81` |
| 3 | can: raw: use a private mutex instead of lock_sock() | Oliver Hartkopp | `c18ce101f2e4` |
| 4 | can: isotp: use a private mutex instead of lock_sock() | Oliver Hartkopp | `e057dd3fc20f` |
| 5 | can: bcm: use a private mutex instead of lock_sock() | Oliver Hartkopp | `ffd980f976e7` |
| 6 | can: isotp: always start the rx timeout in ISOTP_WAIT_DATA state | Oliver Hartkopp | `e057dd3fc20f` |
| 7 | can: isotp: reject socket options while a transfer is active | Oliver Hartkopp | `e057dd3fc20f` |
| 8 | can: netlink: fix static FD-NON-ISO mode validation | Zhu Ling | `6742ca18cb41` |

- **Patch 1 bis 5** sind unverändert die v5: Patch 1 und 2 vermeiden
  RTNL-Stalls in CAN_BCM, Patch 3 bis 5 ersetzen `lock_sock()` durch den
  Mutex `conf_lock`, damit die generischen `SOL_SOCKET`-Optionen die
  Notifier nicht mehr unter RTNL aufhalten können. Patch 3 und 4 brauchen
  den Commit 43c973a0887d, Patch 5 braucht Patch 1 und 2.
- **Patch 6** startet den Empfangs-Timeout in `isotp_rcv_ff()` und
  `isotp_rcv_cf()`, bevor ein Flow Control gesendet wird. Ohne ihn bleibt
  `so->rx.state` ohne Timer in `ISOTP_WAIT_DATA` stehen, wenn das Flow
  Control nicht gesendet werden kann oder im Listen-Mode gar nicht
  gesendet wird; nach dem Entfernen des Devices lehnt `isotp_bind()` den
  Socket dann dauerhaft mit `-EAGAIN` ab. Im Listen-Mode meldet ein First
  Frame ohne Folge-Frames jetzt `ETIMEDOUT`, wie eine Lücke mitten im
  Block es schon tut.
- **Patch 7** prüft in `isotp_setsockopt_locked()` zusätzlich zu
  `so->bound`, dass Sende- und Empfangszustand idle sind, wie
  `isotp_bind()` es schon tut. Anlass ist das Sashiko-Review zu Patch 4
  im Pull-Request. Patch 6 muss vorher kommen, sonst würde ein hängender
  Empfangszustand zusätzlich `setsockopt()` sperren.
- **Patch 8** ist Zhu Lings Fix aus dem Pull-Request, nach dem
  Sashiko-Review überarbeitet: Statt die statischen Modi nach dem Update
  wiederherzustellen, wird eine Anfrage, die einen statischen Modus
  ausschaltet, mit eigener Fehlermeldung abgelehnt, unabhängig vom
  resultierenden FD-Zustand. Der Commit-Text beschreibt die volle
  Auswirkung. Zhu Ling bleibt Autor, die Überarbeitung ist als
  `[Hartkopp: ...]`-Notiz vermerkt. Zhus übrige Netlink-Patches aus dem
  Pull-Request (5/9 und 7/9) wenden unverändert auf Patch 8 an.

## Patches 9 und 10: Folgepatches für can-next (kein Fix, nicht stable)

| # | Patch |
|---|---|
| 9 | can: raw: read socket options under conf_lock in raw_getsockopt() |
| 10 | can: isotp: read socket options under conf_lock in isotp_getsockopt() |

Beide lesen die Optionswerte unter `conf_lock` in eine lokale Variable und
kopieren sie erst nach `mutex_unlock()` in den User-Space. Sie setzen auf
Patch 3 bzw. 4 auf und stellen den Struct-Kommentar auf "sockopts".

Diese beiden Patches sind neu geschrieben und noch nicht gegengelesen;
der Signed-off-by des Autors ist als Vorschlag eingetragen.

## Patch 11: memcg-Abrechnung für can-next (zurückgestellt)

| # | Patch |
|---|---|
| 11 | can: enable memcg accounting for user triggered allocations |

Der für v5 vorbereitete Stand ohne Abrechnung des isotp-RX-Puffers in
`isotp_rcv_ff()` (dort nur ein Kommentar), auf Patch 10 aufgesetzt. Der
Code ist gegenüber der vorbereiteten Fassung unverändert, die
Changelog-Notizen unter dem `---` sind übernommen. Der Patch war Teil der
Serie bis v4 und wird erst verschickt, wenn die Fixes in can-next
angekommen sind; Changelog und Links sind dann anzupassen.

## Basis

Mainline `067c5c24ce` (10.11.2026). Die Mails der v6 nennen als Basis
`30c71476d842` aus dem net-Tree; die betroffenen Dateien sind dort
identisch.

## Prüfung

- Die Dateien 1 bis 11 wenden in dieser Reihenfolge per `git am` auf die
  Basis an.
- `net/can/` und `drivers/net/can/dev/` übersetzen nach der v6 und nach
  jedem der Patches 9 bis 11 fehler- und warnungsfrei (gcc 13.3, `W=1`,
  mit `CONFIG_PROVE_LOCKING`, `CONFIG_DEBUG_MUTEXES` und
  `CONFIG_PROC_FS`). Kein vollständiger Kernel-Build.
- Patch 1 bis 7 sind mit der Test-Suite (`sockopt_stall`,
  `sockopt_churn`, `shared_sock`, `isotp_state_test` u. a.) unter lockdep
  und KASAN gelaufen. Nachweis für Patch 6 und 7 mit `isotp_state_test`:
  ohne beide schlagen alle vier Fälle fehl, mit beiden bestehen sie (Lauf
  vom 16.11.2026 auf `7.4.0-rc3-locktest`, long, `debug_locks` danach 1).
  Ein fehlgeschlagenes Flow Control im normalen Modus ist von User-Space
  aus nicht gezielt auslösbar und nicht eigens getestet.
- Patch 8 ist nur übersetzt, nicht auf M_CAN- oder pcan_usb_fd-Hardware
  getestet.
- Patch 9 und 10 sind nur übersetzt. Als Funktionstest bietet sich
  `sockopt_test` aus der Test-Suite an, das alle CAN_RAW- und
  CAN_ISOTP-Optionen setzt und zurückliest.
- Patch 11 ist nur übersetzt; die memcg-Abrechnung selbst ist ungetestet.
- checkpatch meldet nichts außer den bei mir unbekannten Commit-IDs in
  den `Fixes:`-Zeilen.

## followup/: Fix zu Patch 6 (Sashiko-Review)

`followup/0001-can-isotp-check-the-CF-length-before-stopping-the-rx.patch`
verschiebt in `isotp_rcv_cf()` die beiden CF-Längenprüfungen vor
`hrtimer_cancel()`. Ein ungültiger CF wird damit verworfen, ohne den
laufenden Empfangs-Timeout anzuhalten; jeder Return nach
`hrtimer_cancel()` beendet den Empfang oder startet den Timeout neu.
`Reported-by: Sashiko` mit `Closes:` auf das Review zu Patch 6
(`179504035916.3136.12986898667697830880@kernel.org`), `Fixes:
e057dd3fc20f`, `Cc: stable`.

Basis: Patches 1 bis 7 auf `067c5c24ce`. `net/can/` übersetzt mit `W=1`
fehler- und warnungsfrei, checkpatch meldet nur die bei mir unbekannte
Commit-ID in `Fixes:`. Kein Laufzeittest; `isotp_state_test` hat noch
keinen Fall mit ungültigem CF.

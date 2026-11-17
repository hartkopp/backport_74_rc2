# can_mutex: RTNL-Stalls in CAN_RAW, CAN_ISOTP und CAN_BCM, Folgepatches

Mainline-Patches, keine Stable-Backports.

## Patches 1 bis 5: Serie v5 (Fixes, für stable markiert)

"[PATCH v5 0/5] can: avoid RTNL stalls in CAN_RAW, CAN_ISOTP and CAN_BCM",
unverändert die mit b4 erzeugten Mails vom 13.11.2026 (lokale Ausgabe,
die Message-IDs der verschickten Serie weichen ab).

| # | Patch | Fixes |
|---|---|---|
| 1 | can: bcm: copy the CAN frames outside of lock_sock() | `ffd980f976e7` |
| 2 | can: bcm: do not remove the procfs entry in bcm_notify() | `76fe372ccb81` |
| 3 | can: raw: use a private mutex instead of lock_sock() | `c18ce101f2e4` |
| 4 | can: isotp: use a private mutex instead of lock_sock() | `e057dd3fc20f` |
| 5 | can: bcm: use a private mutex instead of lock_sock() | `ffd980f976e7` |

Patch 3 bis 5 ersetzen `lock_sock()` durch den Mutex `conf_lock` in der
jeweiligen Socket-Struktur, damit die generischen `SOL_SOCKET`-Optionen
die Notifier nicht mehr unter RTNL aufhalten können. Patch 3 und 4
brauchen den Commit 43c973a0887d, Patch 5 braucht Patch 1 und 2.

## Patches 6 und 7: isotp-Fixes (für stable, eigene Patches)

| # | Patch | Fixes |
|---|---|---|
| 6 | can: isotp: always start the rx timeout in ISOTP_WAIT_DATA state | `e057dd3fc20f` |
| 7 | can: isotp: reject socket options while a transfer is active | `e057dd3fc20f` |

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
  `isotp_bind()` es schon tut. Anlass ist ein Sashiko-Review zum
  isotp-Mutex-Patch im Pull-Request vom 15.11.2026; das Problem bestand
  schon vorher.

Die Reihenfolge ist wichtig: Patch 7 allein würde einen hängenden
Empfangszustand zusätzlich für `setsockopt()` sperren. Beide setzen auf
Patch 5 auf. Neu geschrieben und noch nicht gegengelesen; der
Signed-off-by des Autors ist als Vorschlag eingetragen.

Nachweis mit `isotp_state_test` aus der Test-Suite: ohne Patch 6 und 7
schlagen alle vier Fälle fehl, mit beiden bestehen sie (Lauf vom
16.11.2026 auf `7.4.0-rc3-locktest`, long, `debug_locks` danach 1).

## Patches 8 und 9: Folgepatches für can-next (kein Fix, nicht stable)

| # | Patch |
|---|---|
| 8 | can: raw: read socket options under conf_lock in raw_getsockopt() |
| 9 | can: isotp: read socket options under conf_lock in isotp_getsockopt() |

Beide lesen die Optionswerte unter `conf_lock` in eine lokale Variable und
kopieren sie erst nach `mutex_unlock()` in den User-Space. Sie setzen auf
Patch 3 bzw. 4 auf und stellen den Struct-Kommentar auf "sockopts".

Diese beiden Patches sind neu geschrieben und noch nicht gegengelesen;
der Signed-off-by des Autors ist als Vorschlag eingetragen.

## Patch 10: memcg-Abrechnung für can-next (zurückgestellt)

| # | Patch |
|---|---|
| 10 | can: enable memcg accounting for user triggered allocations |

Der für v5 vorbereitete Stand ohne Abrechnung des isotp-RX-Puffers in
`isotp_rcv_ff()` (dort nur ein Kommentar), auf Patch 9 aufgesetzt. Der
Code ist gegenüber der vorbereiteten Fassung unverändert, die
Changelog-Notizen unter dem `---` sind übernommen. Der Patch war Teil der
Serie bis v4 und wird erst verschickt, wenn die Fixes in can-next
angekommen sind; Changelog und Links sind dann anzupassen.

## Basis

Mainline `067c5c24ce` (10.11.2026). Die Mails der v5 nennen als Basis
`30c71476d842` aus dem net-Tree; die betroffenen Dateien sind dort
identisch.

## Prüfung

- Die Dateien 1 bis 10 wenden in dieser Reihenfolge per `git am` auf die
  Basis an.
- `net/can/` übersetzt nach jedem der Patches 5 bis 10 fehler- und
  warnungsfrei (gcc 13.3, `W=1`, mit `CONFIG_PROVE_LOCKING`,
  `CONFIG_DEBUG_MUTEXES` und `CONFIG_PROC_FS`). Kein vollständiger
  Kernel-Build.
- Der Code von Patch 1 bis 5 entspricht bis auf die Struct-Kommentare dem
  Stand, der mit der Test-Suite (`sockopt_stall`, `sockopt_churn`,
  `shared_sock` u. a.) unter lockdep und KASAN gelaufen ist.
- Patch 6 und 7 sind mit der Test-Suite gelaufen (siehe oben). Ein
  fehlgeschlagenes Flow Control im normalen Modus ist von User-Space aus
  nicht gezielt auslösbar und nicht eigens getestet.
- Patch 8 und 9 sind nur übersetzt. Als Funktionstest bietet sich
  `sockopt_test` aus der Test-Suite an, das alle CAN_RAW- und
  CAN_ISOTP-Optionen setzt und zurückliest.
- Patch 10 ist nur übersetzt; die memcg-Abrechnung selbst ist ungetestet.
- checkpatch meldet für Patch 6 bis 10 nichts außer den bei mir
  unbekannten Commit-IDs in den `Fixes:`-Zeilen.

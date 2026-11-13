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

## Patches 6 und 7: Folgepatches für can-next (kein Fix, nicht stable)

| # | Patch |
|---|---|
| 6 | can: raw: read socket options under conf_lock in raw_getsockopt() |
| 7 | can: isotp: read socket options under conf_lock in isotp_getsockopt() |

Beide lesen die Optionswerte unter `conf_lock` in eine lokale Variable und
kopieren sie erst nach `mutex_unlock()` in den User-Space. Sie setzen auf
Patch 3 bzw. 4 auf und stellen den Struct-Kommentar auf "sockopts".

Diese beiden Patches sind neu geschrieben und noch nicht gegengelesen;
der Signed-off-by des Autors ist als Vorschlag eingetragen.

## Patch 8: memcg-Abrechnung für can-next (zurückgestellt)

| # | Patch |
|---|---|
| 8 | can: enable memcg accounting for user triggered allocations |

Der für v5 vorbereitete Stand ohne Abrechnung des isotp-RX-Puffers in
`isotp_rcv_ff()` (dort nur ein Kommentar), auf Patch 7 aufgesetzt. Der
Code ist gegenüber der vorbereiteten Fassung unverändert, die
Changelog-Notizen unter dem `---` sind übernommen. Der Patch war Teil der
Serie bis v4 und wird erst verschickt, wenn die Fixes in can-next
angekommen sind; Changelog und Links sind dann anzupassen.

## Basis

Mainline `067c5c24ce` (10.11.2026). Die Mails der v5 nennen als Basis
`30c71476d842` aus dem net-Tree; die betroffenen Dateien sind dort
identisch.

## Prüfung

- Alle acht Dateien wenden in dieser Reihenfolge per `git am` auf die
  Basis an.
- `net/can/` übersetzt nach Patch 5, 6, 7 und 8 fehler- und warnungsfrei
  (gcc 13.3, `W=1`, mit `CONFIG_PROVE_LOCKING`, `CONFIG_DEBUG_MUTEXES` und
  `CONFIG_PROC_FS`). Kein vollständiger Kernel-Build.
- Der Code von Patch 1 bis 5 entspricht bis auf die Struct-Kommentare dem
  Stand, der mit der Test-Suite (`sockopt_stall`, `sockopt_churn`,
  `shared_sock` u. a.) unter lockdep und KASAN gelaufen ist.
- Patch 6 und 7 sind nur übersetzt, nicht gelaufen. Als Funktionstest
  bietet sich `sockopt_test` aus der Test-Suite an, das alle CAN_RAW- und
  CAN_ISOTP-Optionen setzt und zurückliest.
- checkpatch meldet für Patch 6 und 7 nichts.
- Patch 8 ist nur übersetzt; die memcg-Abrechnung selbst ist ungetestet.

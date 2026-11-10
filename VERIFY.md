# Top-Level-Verifikation der Backports

Wie in `bcm_stable` liegen die finalen Stände aller vom Set berührten Dateien
für master und jeden Branch nebeneinander in [`finsrc/`](finsrc/), zum Diffen
z.B. mit `mgdiff`:

| Datei | finsrc-Name |
|---|---|
| `net/can/af_can.c`, `bcm.c`, `gw.c`, `isotp.c`, `raw.c` | `af_can-<tag>.c`, `bcm-<tag>.c`, … |
| `include/linux/can/can-ml.h` | `can-ml-<tag>.h` |
| `include/net/netns/can.h` | `netns-can-<tag>.h` |

`<tag>` ist `master` (= `43c973a0887d`, #5 in Linus' Tree) bzw. `510`, `515`,
`61`, `66`, `612`, `618` (= Branch-Spitze + gequeuete Patches + Serie).
[`finsrc/pre/`](finsrc/pre/) enthält dieselben Dateien **vor** der Serie:
master = `962947b69589^` + `874f5f14cf62` (#3, liegt in master zwischen #2
und #4 und ist in den Branches bereits gequeuet), Branches = Spitze +
gequeuete Patches.

## Diff der Diffs

[`scripts/diffdiff.py`](scripts/diffdiff.py) vergleicht pro Datei, Branch und
Funktion bzw. Struct den Unterschied *master ↔ Branch* vor und nach der Serie.
Ein exakter Backport lässt diesen Unterschied unverändert. Jede gemeldete
Funktion ist damit eine Stelle, an der der Backport etwas anderes tut als
der Upstream-Patch in master: eine Anpassung, oder etwas Vergessenes.
Mehrzeilige Ausdrücke werden vor dem Vergleich zusammengefügt, reines
Umbrechen fällt also nicht auf.

```sh
scripts/diffdiff.py [finsrc] [--branch X.Y] [--file raw.c]
```

Zeilen im Bericht: `before|after` = Unterschied vor/nach der Serie,
`master|branch` = Zeile nur auf dieser Seite. Wurde ein Block upstream
komplett umgebaut (`raw_setsockopt()` durch #5), stehen stattdessen die
Upstream- und die Backport-Änderung des Blocks nebeneinander.

Vollständige Ausgabe: [`finsrc/diffdiff-report.txt`](finsrc/diffdiff-report.txt)

## Ergebnis

| Datei | 5.10 | 5.15 | 6.1 | 6.6 | 6.12 | 6.18 |
|---|---|---|---|---|---|---|
| `bcm.c` | = | = | = | = | = | = |
| `gw.c` | = | = | = | = | = | = |
| `isotp.c` | = | = | = | = | = | = |
| `can-ml.h` | = | = | = | = | = | = |
| `netns/can.h` | = | = | = | = | = | = |
| `af_can.c` | A | A | A | A | A | A |
| `raw.c` | B, C, D, E, F, P | B, C, D, E | B, C, D, E | B, C, D, E | B, C, D, E | E |

`=` heißt: Der Unterschied zu master ist vor und nach der Serie identisch,
der Backport tut also exakt dasselbe wie Upstream. Die Buchstaben verweisen
auf die Befunde unten. **Jeder Befund ist eine dokumentierte Anpassung,
nichts deutet auf eine vergessene Änderung hin.**

| | Funktion | Befund | Notiz im Patch |
|---|---|---|---|
| A | `can_rcv()`, `canfd_rcv()`, `canxl_rcv()` (ab 6.1) | Nur `dev->type != ARPHRD_CAN \|\|` entfällt, upstream steht zusätzlich `!csx` | #2: kein `can_skb_ext` im Baum |
| B | `raw_release()` | `sock_net(sk)` statt `net` | #4: keine lokale Variable `net` |
| C | `raw_setsockopt()` (+ `_locked`) | Backport-Änderung = RTNL raus, `reg_state`-Shortcut mit Kommentaren wie upstream; Upstream baut die Funktion zusätzlich durch #5 um | #4: kein `raw_setsockopt_locked()`; #5: kopiert hier schon vor `lock_sock()` |
| D | `raw_setsockopt()` in 5.10/5.15 | `dev->reg_state` ohne `READ_ONCE()` | #4: `reg_state` ist hier ein Bitfeld |
| E | `raw_getsockopt()` | `copy_to_user()` statt `copy_to_iter()`; `put_user()` für `-ERANGE` hinter `release_sock()` (5.10: kein `-ERANGE`, Kürzen bleibt) | #5: kein `getsockopt_iter` |
| F | `raw_bind()`, `struct raw_sock` in 5.10 | `dev_hold()`/`dev_put()` statt `netdev_hold()`/Tracker, NULL-Prüfung vor `dev_put()` | #4: ungetrackte Referenz |
| P | `raw_notify()`, `raw_init()`, `raw_release()`, `raw_bind()` in 5.10 | Die `before`-Unterschiede verschwinden: Die Voraussetzungen `ee8b94c8510c`, `11c9027c983e`, `c275a176e4b6` gleichen `raw.c` an den Stand der anderen Branches an (`ro->dev` statt `ifindex`-Lookup) | 5.10-Voraussetzungen |

In 5.15 bis 6.12 ist `ro->dev` bereits vorhanden; die ungetrackten
Referenzen dort (`so->dev` bis 6.12, `ro->dev` bis 5.15) sind keine Änderung
gegenüber dem Vorher-Stand und tauchen deshalb nicht auf.

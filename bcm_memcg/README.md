# bcm_memcg: vorbereitete Stable-Backports

Backports der Serie
"[PATCH v3 0/3] can: bcm: avoid RTNL stalls and enable memcg accounting"
(`20261109-can-bcmlock-memcg-v3-0-3ce0f63e90ae@hartkopp.net`, linux-can)
für linux-5.10.y bis linux-6.18.y.

**Status: vorbereitet, noch nicht versandfertig.** Die Serie ist noch nicht
in Mainline. Vor dem Versenden fehlt pro Patch:

- die Zeile `commit <40-stellige ID> upstream.` am Anfang der Commit-Message
  (wie bei den Patches in `../linux-X.Y.y/`),
- die Trailer, die beim Einspielen upstream dazukommen (`Link:`,
  `Signed-off-by:` des Maintainers), vor der `[ backport to X.Y: ... ]`-Notiz,
- ein Abgleich mit der Fassung, die upstream tatsächlich landet (falls es
  noch ein v4 gibt),
- die `--in-reply-to`-Referenz (es gibt noch keine FAILED-Mails).

## Patches

Pro Branch drei Dateien in `linux-X.Y.y/`:

| # | Betreff | Cc: stable | 6.18 | 6.12 | 6.6 | 6.1 | 5.15 | 5.10 |
|---|---|---|---|---|---|---|---|---|
| 1 | can: bcm: copy the CAN frames outside of lock_sock() | ja | unverändert | unverändert | unverändert | unverändert | unverändert | unverändert |
| 2 | can: bcm: do not remove the procfs entry in bcm_notify() | ja | Kontext | Kontext | Kontext | Kontext | Kontext | Kontext |
| 3 | can: enable memcg accounting for user triggered allocations | nein | angepasst | angepasst | angepasst | angepasst | angepasst | angepasst |

Patch 3 hat upstream weder `Fixes:` noch `Cc: stable` (siehe Cover Letter)
und liegt hier nur für den Fall bereit, dass er doch nach stable soll.
Patch 1 und 2 hängen nicht von ihm ab.

## Basis

Spitze von `linux-X.Y.y` (Stand 06.11.2026) plus `../linux-X.Y.y/queued/`
plus die Serie aus `../linux-X.Y.y/[123]-*/`. Die Backports setzen also
voraus, dass 962947b69589, 0f3ad9ab40e3 und 43c973a0887d im jeweiligen
Stable-Baum liegen (Patch 3 berührt in `af_can.c` und `raw.c` Stellen,
die diese Serie geändert hat).

## Anpassungen

Patch 1 wendet überall unverändert an und hat deshalb keine Notiz. Bei
Patch 2 und 3 steht die Anpassung als `[ backport to X.Y: ... ]`-Notiz in der
Commit-Message.

- **Patch 2**, alle Branches: nur Kontext. `bcm_proc_show()` gibt hier noch
  die Socket-Pointer aus, `bcm_connect()` erzeugt den Namen mit `sprintf()`.
  In 5.10 zusätzlich `sk->sk_error_report()` im Kontext von `NETDEV_DOWN`.
  Die Änderung selbst ist identisch mit Upstream.
- **Patch 3**:
  - alle Branches: `kzalloc(..., GFP_KERNEL_ACCOUNT)` statt `kzalloc_obj()`
    in `can_pernet_init()` und `j1939_priv_create()`.
  - bis 6.12: Die Filter-Allokation für `CAN_RAW_FILTER` steht an anderer
    Stelle in `raw_setsockopt()` (kein `raw_setsockopt_locked()`-Umbau).
  - bis 6.1: Der isotp-Teil entfällt, es gibt dort keinen dynamisch
    allozierten TX-Puffer (`max_pdu_size`).
  - 5.15/5.10: Kontext in `raw_init()`.

## Prüfung

- Die Patch-Dateien lassen sich auf die oben genannte Basis anwenden
  (`git apply --whitespace=error-all`) und ergeben denselben Stand wie der
  Arbeitsbaum, aus dem sie exportiert wurden.
- Compile-Test nur von `net/can/` nach jedem einzelnen Patch, mit
  `../configs/linux-X.Y.y.config` plus `CONFIG_PROC_FS=y`. Kein
  vollständiger Kernel-Build, kein Laufzeittest. Ergebnis: alle sechs
  Branches nach jedem Patch fehler- und warnungsfrei (gcc 13.3).

Hinweis: In `../configs/linux-5.10.y.config` ist `CONFIG_PROC_FS` nicht
gesetzt (in den anderen Configs schon). Damit wird der procfs-Code in
`bcm.c`, den Patch 2 ändert, auf 5.10 von `../scripts/build-all.sh` nicht
übersetzt. Für einen Build-Test dieser Patches dort `CONFIG_PROC_FS=y`
ergänzen. `CONFIG_MEMCG` ist in keiner der Configs gesetzt; für den
Compile-Test von Patch 3 ist das unerheblich, für einen Funktionstest nicht.

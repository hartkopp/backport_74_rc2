# can_mutex: privater Mutex statt lock_sock()

Drei Mainline-Patches, die `lock_sock()` in CAN_RAW, CAN_ISOTP und CAN_BCM
durch den Mutex `conf_lock` in der jeweiligen Socket-Struktur ersetzen,
damit die generischen `SOL_SOCKET`-Optionen die Notifier nicht mehr unter
RTNL aufhalten können.

| Patch | Datei | Fixes |
|---|---|---|
| can: raw: use a private mutex instead of lock_sock() | `0001-can-raw-use-a-private-mutex-instead-of-lock_sock.patch` | `c18ce101f2e4` |
| can: isotp: use a private mutex instead of lock_sock() | `0002-can-isotp-use-a-private-mutex-instead-of-lock_sock.patch` | `e057dd3fc20f` |
| can: bcm: use a private mutex instead of lock_sock() | `0003-can-bcm-use-a-private-mutex-instead-of-lock_sock.patch` | `ffd980f976e7` |

Alle drei tragen `Fixes:` und `Cc: stable@vger.kernel.org` mit
Abhängigkeitsvermerk (`# depends on "..."`). Die Fixes-Ziele sind die
Commits, die das jeweilige Protokoll eingeführt haben (wie bei 43c973a0887d
und dem bcm-Frame-Kopie-Patch); in der Git-Historie nachgeprüft ist das
hier nicht.

Dies sind Mainline-Patches, keine Stable-Backports.

## Position in der Serie

Gedacht als Teil einer v4 von "can: bcm: avoid RTNL stalls and enable memcg
accounting", vor dem memcg-Patch, der nicht für stable markiert ist:

1. can: bcm: copy the CAN frames outside of lock_sock()
2. can: bcm: do not remove the procfs entry in bcm_notify()
3. can: raw: use a private mutex instead of lock_sock()
4. can: isotp: use a private mutex instead of lock_sock()
5. can: bcm: use a private mutex instead of lock_sock()
6. can: enable memcg accounting for user triggered allocations

Basis der Patch-Dateien: Mainline `067c5c24ce` (10.11.2026) plus 1 und 2.
Patch 5 braucht 1 und 2, Patch 3 und 4 brauchen den Commit 43c973a0887d.

## Einfügen in den b4-Branch

Im Kernel-Tree auf dem b4-Branch der Serie, der memcg-Patch ist der
oberste Commit:

```sh
git tag bcm-memcg-before-mutex          # Sicherung
MEMCG=$(git rev-parse HEAD)
git reset --hard HEAD~1                 # memcg-Patch vorübergehend weg
git am <pfad>/backport_74_rc2/can_mutex/000[123]-*.patch
git cherry-pick $MEMCG
```

Danach Cover Letter anpassen (`b4 prep --edit-cover`) und prüfen
(`b4 prep --check`).

## Prüfung

- Die Reihenfolge 1 bis 6 wendet auf Mainline `067c5c24ce` sauber an; das
  Einfügen wie oben beschrieben wurde an einem nachgebauten Branch
  durchgespielt (inkl. `git cherry-pick` des memcg-Patches ohne Konflikt).
- `net/can/` übersetzt nach jedem der Patches 3 bis 6 fehler- und
  warnungsfrei (gcc 13.3, `W=1`, mit `CONFIG_PROVE_LOCKING`,
  `CONFIG_DEBUG_MUTEXES` und `CONFIG_PROC_FS`). Kein vollständiger
  Kernel-Build, kein Laufzeittest.
- Nach Patch 5 gibt es in `raw.c`, `isotp.c` und `bcm.c` kein
  `lock_sock()`/`release_sock()` mehr.
- checkpatch meldet bei Patch 3 und 4 den Commit-Verweis auf 43c973a0887d,
  weil der Titel über den Zeilenumbruch geht; sonst nichts.

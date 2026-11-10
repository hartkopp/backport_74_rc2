# can_mutex: privater Mutex statt lock_sock()

Drei Mainline-Patches, die `lock_sock()` in CAN_RAW, CAN_ISOTP und CAN_BCM
durch den Mutex `conf_lock` in der jeweiligen Socket-Struktur ersetzen,
damit die generischen `SOL_SOCKET`-Optionen die Notifier nicht mehr unter
RTNL aufhalten können.

| Patch | Datei |
|---|---|
| can: raw: use a private mutex instead of lock_sock() | `0001-can-raw-use-a-private-mutex-instead-of-lock_sock.patch` |
| can: isotp: use a private mutex instead of lock_sock() | `0002-can-isotp-use-a-private-mutex-instead-of-lock_sock.patch` |
| can: bcm: use a private mutex instead of lock_sock() | `0003-can-bcm-use-a-private-mutex-instead-of-lock_sock.patch` |

**Status: Entwurf für Mainline, keine Stable-Backports.** Die Patches haben
weder `Fixes:` noch `Cc: stable`.

## Basis

Mainline `067c5c24ce` (10.11.2026) plus die Serie
"[PATCH v3 0/3] can: bcm: avoid RTNL stalls and enable memcg accounting"
(siehe [`../bcm_memcg/`](../bcm_memcg/)). Patch 3 setzt bcm-Patch 1 und 2
dieser Serie voraus, Patch 1 und 2 den Commit 43c973a0887d.

## Prüfung

- Wenden auf die Basis sauber an (`git am`).
- `net/can/` übersetzt nach jedem einzelnen Patch fehler- und warnungsfrei
  (gcc 13.3, `W=1`, mit `CONFIG_PROVE_LOCKING`, `CONFIG_DEBUG_MUTEXES` und
  `CONFIG_PROC_FS`). Kein vollständiger Kernel-Build, kein Laufzeittest.
- Nach der Serie gibt es in `raw.c`, `isotp.c` und `bcm.c` kein
  `lock_sock()`/`release_sock()` mehr.
- checkpatch meldet bei Patch 1 und 2 den Commit-Verweis auf 43c973a0887d,
  weil der Titel über den Zeilenumbruch geht; sonst nichts.

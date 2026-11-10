# backport_74_rc2

Backports der net/can-Patches aus Linux 7.4-rc2, die beim Einspielen in die
stable-Branches 5.10.y, 5.15.y, 6.1.y, 6.6.y, 6.12.y und 6.18.y mit
"FAILED: patch ... failed to apply" zurückkamen.

Betroffen sind drei zusammenhängende Upstream-Commits, die pro Branch als
Serie eingereicht werden:

1. `962947b69589` can: replace ARPHRD_CAN type checks with can_get_ml_priv()
2. `0f3ad9ab40e3` can: protect the receive lists with a per-device lock
3. `43c973a0887d` can: raw, isotp: copy socket options outside of lock_sock()

Für 5.10 kommen drei ältere `raw.c`-Fixes als Voraussetzung davor, die dort
nie gelandet sind (siehe [linux-5.10.y/README.md](linux-5.10.y/README.md)).

## Aufbau

| Pfad | Inhalt |
|---|---|
| [`STATUS.md`](STATUS.md) | Auswertung der Statusmails: welcher Patch auf welchem Branch OK/FAILED, Prüfung gegen gregkh/linux, Backport-Status |
| [`mails/`](mails/) | Statusmails von Sasha Levin (`.eml`) |
| `linux-X.Y.y/[123]-<sha>/*.patch` | Versandfertige Backports pro Branch, ein Verzeichnis pro FAILED-Mail (`git format-patch`) |
| `linux-X.Y.y/queued/` | Bereits gequeuete Patches, auf denen die Serie aufsetzt (nur für den Build-Test) |
| `linux-X.Y.y/README.md` | Anpassungen, Prüfliste und `git send-email`-Befehl pro Branch |
| [`configs/`](configs/) | Minimale Kernel-Configs (allnoconfig + CAN) pro Branch |
| [`scripts/`](scripts/) | Build-Test-Scripts |
| [`finsrc/`](finsrc/), [`VERIFY.md`](VERIFY.md) | Finale Dateistände master/Branches und "Diff der Diffs"-Verifikation |

Erarbeitet wurden die Backports auf dem Mirror
[gregkh/linux](https://github.com/gregkh/linux), Stand der Branch-Spitzen
vom 06.11.2026 (5.10.274, 5.15.225, 6.1.192, 6.6.162, 6.12.116, 6.18.62).
Jeder Patch wurde per `git am` auf die jeweilige Basis zurückgespielt und mit
dem Arbeitsstand verglichen (identisch). Alle Branches bauen mit den
Minimal-Configs nach jedem einzelnen Patch (`scripts/build-all.sh -e`).

## Build-Test

Ein Branch:

```sh
scripts/build-branch.sh [-e] [-b <base-ref>] <linux-stable-tree> <X.Y>
```

Das Script legt im lokalen linux-stable-Tree den Branch `bp-test/X.Y` auf
`origin/linux-X.Y.y` (oder `-b <base-ref>`) neu an, wendet die Patches aus
`queued/` an (übersprungen, wenn sie in der Basis schon enthalten sind) und
danach die Serie. Gebaut wird mit

```sh
cp configs/linux-X.Y.y.config /ramdisk/.config
make O=/ramdisk olddefconfig
KBUILD_BUILD_TIMESTAMP='' make O=/ramdisk CC="ccache gcc" -j16
```

Mit `-e` wird nach jedem einzelnen Patch der Serie gebaut (Bisect-Fähigkeit),
sonst einmal am Ende. `OBJ`, `JOBS` und `CC_CMD` lassen sich per Umgebung
überschreiben.

Alle Branches nacheinander, mit Zusammenfassung und Logs `build-X.Y.log` im
aktuellen Verzeichnis:

```sh
scripts/build-all.sh [-e] <linux-stable-tree> [<X.Y> ...]
```

Der linux-stable-Tree darf keine uncommitteten Änderungen haben. Vorher die
stable-Branches fetchen (`git fetch origin`).

Abbruch (Strg-C) und Neustart mit demselben Befehl sind unkritisch: Der
Testbranch wird bei jedem Lauf neu auf die Basis gesetzt, ein durch den
Abbruch liegengebliebenes `git am` auf einem `bp-test/*`-Branch wird
automatisch mit `git am --abort` aufgeräumt (ein `git am` auf einem anderen
Branch führt dagegen zum Abbruch des Scripts), und abgebrochene
Objektdateien entfernt make selbst.

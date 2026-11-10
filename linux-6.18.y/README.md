# Patch-Set für linux-6.18.y

Pro FAILED-Mail ein eigener Thread, jeweils als Antwort auf diese Mail
(Aufbau wie Sashas eigene Backport-Antworten auf stable@). Die Threads
bauen aufeinander auf und werden in der Reihenfolge 1 → 2 → 3 verschickt.

| Thread | antwortet auf FAILED-Mail | Patch | Upstream-Commit | Betreff |
|---|---|---|---|---|
| 1 | `20261109200450-failed-6.18-962947b69589@kernel.org` | `1-962947b69589/0001-can-replace-ARPHRD_CAN-type-checks-with-can_get_ml_p.patch` | `962947b69589` | can: replace ARPHRD_CAN type checks with can_get_ml_priv() |
| 2 | `20261109200455-failed-6.18-0f3ad9ab40e3@kernel.org` | `2-0f3ad9ab40e3/0001-can-protect-the-receive-lists-with-a-per-device-lock.patch` | `0f3ad9ab40e3` | can: protect the receive lists with a per-device lock |
| 3 | `20261109200452-failed-6.18-43c973a0887d@kernel.org` | `3-43c973a0887d/0001-can-raw-isotp-copy-socket-options-outside-of-lock_so.patch` | `43c973a0887d` | can: raw, isotp: copy socket options outside of lock_sock() |

Die Patches von Thread 2 und 3 nennen unter dem `---` (fällt beim
Anwenden weg) den bzw. die Backports, auf die sie aufbauen, mit der
Message-ID der jeweiligen FAILED-Mail.

Die Anpassungen gegenüber Upstream stehen jeweils als `[ backport to 6.18: ... ]`-Notiz
in der Commit-Message des Patches.

## Basis

`origin/linux-6.18.y` (Stand Linux 6.18.62) plus die bereits gequeueten
Patches in [`queued/`](queued/). Das Set setzt voraus, dass diese vor ihm angewendet werden.

## Anpassungen (Kurzfassung)

- **can_get_ml_priv()**: Ohne `can_skb_ext` wird in den Empfangsfunktionen nur
  der `ARPHRD_CAN`-Teil der Bedingung entfernt. `raw.c` bekommt das fehlende
  `#include <linux/can/can-ml.h>` (upstream erst mit `faba5860fcf9`).
- **per-device lock**: Nur `kzalloc()`-Kontext in `can_pernet_init()`
  (kein `kzalloc_obj()`), sonst inhaltlich identisch mit Upstream.
- **copy socket options**: `raw_getsockopt()` nutzt hier `copy_to_user()`/
  `put_user()` statt `getsockopt_iter`. Die Filter werden unter `lock_sock()`
  dupliziert und nach `release_sock()` kopiert; ebenso das `put_user()` der
  benötigten Filtergröße bei `-ERANGE`.

## Vor dem Versenden prüfen

1. Build-Test mit `scripts/build-branch.sh -e <linux-stable> 6.18`
   (siehe [README](../README.md)).
2. Sind die Patches aus `queued/` inzwischen in linux-6.18.y gelandet? Falls nicht,
   per kurzer Antwort darauf hinweisen.
3. Jeder Patch trägt bereits ein abschließendes
   `Signed-off-by: Oliver Hartkopp <socketcan@hartkopp.net>` (persönliche
   DCO-Zusicherung) – bitte vorher gegenlesen.

## Versenden

Drei Aufrufe, in dieser Reihenfolge; jeder Thread antwortet auf seine
FAILED-Mail. Bei mehreren Patches in einem Thread (5.10, Thread 1)
antworten die weiteren Patches auf den ersten.

```sh
git send-email --suppress-cc=all --confirm=always \
  --to='stable@vger.kernel.org' \
  --cc='Sasha Levin <sashal@kernel.org>' \
  --cc='Marc Kleine-Budde <mkl@pengutronix.de>' \
  --cc='Oliver Hartkopp <socketcan@hartkopp.net>' \
  --in-reply-to='20261109200450-failed-6.18-962947b69589@kernel.org' --thread --no-chain-reply-to \
  linux-6.18.y/1-962947b69589/*.patch
```

```sh
git send-email --suppress-cc=all --confirm=always \
  --to='stable@vger.kernel.org' \
  --cc='Sasha Levin <sashal@kernel.org>' \
  --cc='Marc Kleine-Budde <mkl@pengutronix.de>' \
  --cc='Oliver Hartkopp <socketcan@hartkopp.net>' \
  --in-reply-to='20261109200455-failed-6.18-0f3ad9ab40e3@kernel.org' --thread --no-chain-reply-to \
  linux-6.18.y/2-0f3ad9ab40e3/*.patch
```

```sh
git send-email --suppress-cc=all --confirm=always \
  --to='stable@vger.kernel.org' \
  --cc='Sasha Levin <sashal@kernel.org>' \
  --cc='Marc Kleine-Budde <mkl@pengutronix.de>' \
  --cc='Oliver Hartkopp <socketcan@hartkopp.net>' \
  --in-reply-to='20261109200452-failed-6.18-43c973a0887d@kernel.org' --thread --no-chain-reply-to \
  linux-6.18.y/3-43c973a0887d/*.patch
```

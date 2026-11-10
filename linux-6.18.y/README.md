# Patch-Set für linux-6.18.y

Antwort auf Sashas FAILED-Mail zu `can: replace ARPHRD_CAN type checks with
can_get_ml_priv()` (Message-ID `20261109200450-failed-6.18-962947b69589@kernel.org`).
Das Set deckt auch die FAILED-Mails zu `can: protect the receive lists with a
per-device lock` und `can: raw, isotp: copy socket options outside of
lock_sock()` ab, die darauf aufbauen.

| Patch | Upstream-Commit | Betreff |
|---|---|---|
| `0001-can-replace-ARPHRD_CAN-type-checks-with-can_get_ml_p.patch` | `962947b69589` | can: replace ARPHRD_CAN type checks with can_get_ml_priv() |
| `0002-can-protect-the-receive-lists-with-a-per-device-lock.patch` | `0f3ad9ab40e3` | can: protect the receive lists with a per-device lock |
| `0003-can-raw-isotp-copy-socket-options-outside-of-lock_so.patch` | `43c973a0887d` | can: raw, isotp: copy socket options outside of lock_sock() |

Die Anpassungen gegenüber Upstream stehen jeweils als `[ oliver: ... ]`-Notiz
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
   im Anschreiben bzw. per Antwort darauf hinweisen.
3. Jeder Patch trägt bereits ein abschließendes
   `Signed-off-by: Oliver Hartkopp <socketcan@hartkopp.net>` (persönliche
   DCO-Zusicherung) – bitte vorher gegenlesen.

## Versenden

```sh
git send-email --suppress-cc=all --confirm=always \
  --to='stable@vger.kernel.org' \
  --cc='Sasha Levin <sashal@kernel.org>' \
  --cc='Marc Kleine-Budde <mkl@pengutronix.de>' \
  --cc='Oliver Hartkopp <socketcan@hartkopp.net>' \
  --in-reply-to='20261109200450-failed-6.18-962947b69589@kernel.org' --thread --no-chain-reply-to \
  linux-6.18.y/0*.patch
```

`0001` antwortet damit auf die FAILED-Mail, die weiteren Patches auf `0001`.

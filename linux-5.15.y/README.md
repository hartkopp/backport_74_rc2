# Patch-Set für linux-5.15.y

Antwort auf Sashas FAILED-Mail zu `can: replace ARPHRD_CAN type checks with
can_get_ml_priv()` (Message-ID `20261109202308-failed-5.15-962947b69589@kernel.org`).
Das Set deckt auch die FAILED-Mails zu `can: protect the receive lists with a
per-device lock` und `can: raw, isotp: copy socket options outside of
lock_sock()` ab, die darauf aufbauen.

| Patch | Upstream-Commit | Betreff |
|---|---|---|
| `0001-can-replace-ARPHRD_CAN-type-checks-with-can_get_ml_p.patch` | `962947b69589` | can: replace ARPHRD_CAN type checks with can_get_ml_priv() |
| `0002-can-protect-the-receive-lists-with-a-per-device-lock.patch` | `0f3ad9ab40e3` | can: protect the receive lists with a per-device lock |
| `0003-can-raw-isotp-copy-socket-options-outside-of-lock_so.patch` | `43c973a0887d` | can: raw, isotp: copy socket options outside of lock_sock() |

Die Anpassungen gegenüber Upstream stehen jeweils als `[ backport to 5.15: ... ]`-Notiz
in der Commit-Message des Patches.

## Basis

`origin/linux-5.15.y` (Stand Linux 5.15.225) plus die bereits gequeueten
Patches in [`queued/`](queued/). Das Set setzt voraus, dass diese vor ihm angewendet werden.

## Anpassungen (Kurzfassung)

- **can_get_ml_priv()**: Ohne `can_skb_ext` wird in den Empfangsfunktionen nur
  der `ARPHRD_CAN`-Teil der Bedingung entfernt. `raw.c` bekommt das fehlende
  `#include <linux/can/can-ml.h>` (upstream erst mit `faba5860fcf9`).
- **per-device lock**: `kzalloc()`-Kontext in `can_pernet_init()`; `so->dev`
  und `ro->dev` halten ungetrackte Referenzen per `dev_hold()`. Da
  `raw_setsockopt_locked()` (aus `1e5185c09058`, nur ab 6.18) fehlt, wird RTNL
  direkt in den Fällen `CAN_RAW_FILTER` und `CAN_RAW_ERR_FILTER` von
  `raw_setsockopt()` entfernt. `raw_bind()` behält die NULL-Prüfung vor
  `dev_put()`, `raw_release()` nutzt `sock_net(sk)`. `dev->reg_state` ist hier
  noch ein Bitfeld und wird deshalb ohne `READ_ONCE()` gelesen.
- **copy socket options**: `raw_setsockopt()` kopiert hier ohnehin schon vor
  `lock_sock()`, daher entfallen die Upstream-Änderungen dort. Es bleiben der
  isotp-Teil (unverändert) und `raw_getsockopt()` (wie bei 6.18: duplizieren
  unter `lock_sock()`, `copy_to_user()`/`put_user()` danach).

## Vor dem Versenden prüfen

1. Build-Test mit `scripts/build-branch.sh -e <linux-stable> 5.15`
   (siehe [README](../README.md)).
2. Sind die Patches aus `queued/` inzwischen in linux-5.15.y gelandet? Falls nicht,
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
  --in-reply-to='20261109202308-failed-5.15-962947b69589@kernel.org' --thread --no-chain-reply-to \
  linux-5.15.y/0*.patch
```

Der Cover-Letter `0000` antwortet auf die FAILED-Mail zu `962947b69589`,
alle Patches hängen als Antwort am Cover-Letter. Die Reihenfolge beim
Anwenden ergibt sich aus der Nummerierung `n/m` im Betreff; der
Cover-Letter nennt zusätzlich die Reihenfolge und alle drei FAILED-Mails,
die mit der Serie erledigt sind. Soll er nicht mitgeschickt werden,
`0000-cover-letter.patch` vorher löschen (dann antwortet `0001` auf die
FAILED-Mail).

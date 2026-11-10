# Patch-Set für linux-5.10.y

Antwort auf Sashas FAILED-Mail zu `can: replace ARPHRD_CAN type checks with
can_get_ml_priv()` (Message-ID `20261109202741-failed-5.10-962947b69589@kernel.org`).
Das Set deckt auch die FAILED-Mails zu `can: protect the receive lists with a
per-device lock` und `can: raw, isotp: copy socket options outside of
lock_sock()` ab, die darauf aufbauen.

| Patch | Upstream-Commit | Betreff |
|---|---|---|
| `0001-can-raw-fix-receiver-memory-leak.patch` | `ee8b94c8510c` | can: raw: fix receiver memory leak |
| `0002-can-raw-fix-lockdep-issue-in-raw_release.patch` | `11c9027c983e` | can: raw: fix lockdep issue in raw_release() |
| `0003-can-raw-add-missing-refcount-for-memory-leak-fix.patch` | `c275a176e4b6` | can: raw: add missing refcount for memory leak fix |
| `0004-can-replace-ARPHRD_CAN-type-checks-with-can_get_ml_p.patch` | `962947b69589` | can: replace ARPHRD_CAN type checks with can_get_ml_priv() |
| `0005-can-protect-the-receive-lists-with-a-per-device-lock.patch` | `0f3ad9ab40e3` | can: protect the receive lists with a per-device lock |
| `0006-can-raw-isotp-copy-socket-options-outside-of-lock_so.patch` | `43c973a0887d` | can: raw, isotp: copy socket options outside of lock_sock() |

Die Anpassungen gegenüber Upstream stehen jeweils als `[ backport to 5.10: ... ]`-Notiz
in der Commit-Message des Patches.

## Basis

`origin/linux-5.10.y` (Stand Linux 5.10.274) plus die bereits gequeueten
Patches in [`queued/`](queued/). Das Set setzt voraus, dass diese vor ihm angewendet werden.

## Anpassungen (Kurzfassung)

- **Voraussetzungen 0001–0003**: `ee8b94c8510c` ("can: raw: fix receiver memory
  leak") samt `11c9027c983e` (lockdep) und `c275a176e4b6` (refcount) sind in
  5.10 nie gelandet, ab 5.15 aber vorhanden. #4/#5 bauen in `raw.c` auf
  `ro->dev` auf. Konflikte nur im Kontext (`free_percpu(ro->uniq)` ist in 5.10
  bereits aus `raw_release()` verschoben); für `c275a176e4b6` wird die
  5.15-Variante mit `dev_hold()`/`dev_put()` verwendet (kein netdev tracker).
  Damit sind 0004–0006 in `raw.c` inhaltlich identisch mit 5.15.
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
  Zusätzlich `sk->sk_error_report(sk)` statt `sk_error_report(sk)` (den
  Helfer gibt es erst ab 5.13).
- **copy socket options**: wie 5.15, aber `raw_getsockopt()` kennt in 5.10 noch
  kein `-ERANGE` und kürzt die Filterliste auf die Puffergröße. Dieses
  UAPI-Verhalten bleibt erhalten, nur die Kopie wandert hinter
  `release_sock()`.

## Vor dem Versenden prüfen

1. Build-Test mit `scripts/build-branch.sh -e <linux-stable> 5.10`
   (siehe [README](../README.md)).
2. Sind die Patches aus `queued/` inzwischen in linux-5.10.y gelandet? Falls nicht,
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
  --in-reply-to='20261109202741-failed-5.10-962947b69589@kernel.org' --thread --no-chain-reply-to \
  linux-5.10.y/0*.patch
```

Der Cover-Letter `0000` antwortet auf die FAILED-Mail zu `962947b69589`,
alle Patches hängen als Antwort am Cover-Letter. Die Reihenfolge beim
Anwenden ergibt sich aus der Nummerierung `n/m` im Betreff; der
Cover-Letter nennt zusätzlich die Reihenfolge und alle drei FAILED-Mails,
die mit der Serie erledigt sind. Soll er nicht mitgeschickt werden,
`0000-cover-letter.patch` vorher löschen (dann antwortet `0001` auf die
FAILED-Mail).

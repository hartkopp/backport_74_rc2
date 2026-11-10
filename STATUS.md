# Stable-Status der net/can-Patches (Stand: Mails vom 10.11.2026)

Erzeugt aus den 48 Statusmails von Sasha Levin in [`mails/`](mails/)
(`FAILED: patch '...' failed to apply ...` / `Patch '...' has been added ...`).
Zugeordnet wird über den 40-stelligen Upstream-Commit-Hash in jeder Mail,
nicht über den Betreff.

Reihenfolge: wie die Commits auf dem Mainline-Tree liegen (`git log --oneline net/can/`,
älteste zuerst).

Legende: **OK** = "has been added", **FAIL** = "failed to apply",
**–** = keine Mail zu diesem Branch erhalten.

| # | Upstream-Commit | Dateien | Betreff | 5.10 | 5.15 | 6.1 | 6.6 | 6.12 | 6.18 | 7.3 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `933bf0fcb325` | isotp.c | can: isotp: check the frame type, not just the length | – | – | OK | OK | OK | OK | OK |
| 2 | `962947b69589` | af_can.c, bcm.c, gw.c, isotp.c, raw.c | can: replace ARPHRD_CAN type checks with can_get_ml_priv() | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | OK |
| 3 | `874f5f14cf62` | isotp.c | can: isotp: check the return values of can_rx_register() in isotp_bind() | OK | OK | OK | OK | OK | OK | OK |
| 4 | `0f3ad9ab40e3` | can-ml.h, netns/can.h, af_can.c, bcm.c, isotp.c, raw.c | can: protect the receive lists with a per-device lock | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | OK |
| 5 | `43c973a0887d` | isotp.c, raw.c | can: raw, isotp: copy socket options outside of lock_sock() | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | OK |
| 6 | `12297f855bbd` | proc.c | can: proc: reset pkg_stats atomics individually | OK | OK | OK | OK | OK | OK | OK |
| 7 | `01b19ed9fa03` | proc.c | can: proc: skip stats calculation after reset in can_stat_update() | OK | OK | OK | OK | OK | OK | OK |

Zusätzlich (nicht in der ursprünglichen Liste, aber im Mail-Satz enthalten):

| Upstream-Commit | Dateien | Betreff | 5.10 | 5.15 | 6.1 | 6.6 | 6.12 | 6.18 | 7.3 |
|---|---|---|---|---|---|---|---|---|---|
| `d74307196492` | drivers/net/can/dev/skb.c, can/dev.h, can/skb.h | can: skb: make echo skb freeing safe in any IRQ context | – | – | – | – | – | – | OK |

## Fixes-/Stable-Tags (aus den 7.3-Mails)

| # | Commit | Fixes | Cc: stable |
|---|---|---|---|
| 1 | `933bf0fcb325` | `fb08cba12b52` can: canxl: update CAN infrastructure for CAN XL frames | ja |
| 2 | `962947b69589` | `4e096a18867a` net: introduce CAN specific pointer in the struct net_device | ja |
| 3 | `874f5f14cf62` | `e057dd3fc20f` can: add ISO 15765-2:2016 transport protocol | ja |
| 4 | `0f3ad9ab40e3` | `20bab8b88baa` can: isotp: fix use-after-free race with concurrent NETDEV_UNREGISTER<br>`8e8cda6d737d` can: initial support for network namespaces | ja |
| 5 | `43c973a0887d` | `c18ce101f2e4` [CAN]: Add raw protocol<br>`1e5185c09058` can: raw: add locking for raw flags bitfield | ja, `# depends on "can: protect the receive lists with a per-device lock"` |
| 6 | `12297f855bbd` | `80b5f90158d1` can: statistics: use atomic access in hot path | ja |
| 7 | `01b19ed9fa03` | `80b5f90158d1` can: statistics: use atomic access in hot path | ja |
| – | `d74307196492` | `ae64438be192`, `0ae89beb283a`, `3ccd4c6167d3`, `39549eef3587` | ja (`stable@kernel.org`) |

## Beobachtungen

- **#3, #6, #7** wenden auf allen Branches sauber an. Hier gibt es nichts zu tun.
- **#1** ist ab 6.1 sauber gequeued. Für 5.10/5.15 gibt es keine Mail.
- **#2, #4, #5** scheitern einheitlich auf 5.10 bis 6.18 und laufen nur auf 7.3.
  Sie hängen zusammen: #5 hängt laut Stable-Tag explizit von #4 ab, und #4 baut
  auf dem `can_get_ml_priv()`-Umbau von #2 auf. Gequeued werden müssen sie
  also als Serie #2 → #4 → #5.
- **#4** hat `Fixes: 20bab8b88baa` – das ist der isotp-NETDEV_UNREGISTER-Fix aus
  der `bcm_stable`-Runde. Die Backports von #4 müssen also auf den Stand
  aufsetzen, mit dem `20bab8b88baa` in den jeweiligen Branch gelandet ist.
- Keine der 18 FAILED-Mails nennt "Possible dependencies".
- **`d74307196492`** (drivers/net/can/dev/skb.c) ist bisher nur für 7.3
  gemeldet. Für die älteren Branches gibt es weder OK noch FAIL.

## Verifikation gegen gregkh/linux (Stand der Branches: 06.11.2026)

Branch-Spitzen: 5.10.274, 5.15.225, 6.1.192, 6.6.162, 6.12.116, 6.18.62.
Die am 10.11. gequeueten Patches sind dort also noch nicht enthalten.

**#1 auf 5.10 und 5.15:** `fb08cba12b52` (CAN XL) ist dort nicht enthalten,
ab 6.1 schon (Teil der Basis). #1 ist für 5.10 und 5.15 also nicht
relevant. Er würde zwar textuell anwenden, setzt aber die mit CAN XL
eingeführten Helfer `can_is_can_skb()`/`can_is_canfd_skb()` voraus.

**`20bab8b88baa` (Fixes-Ziel von #4)** ist in allen sechs Branches gelandet:

| 5.10 | 5.15 | 6.1 | 6.6 | 6.12 | 6.18 |
|---|---|---|---|---|---|
| `f311bbb29bb0` | `8e018f433559` | `33b9cd9245e2` | `0b811c4bbe3e` | `43884dc7963b` | `7bef39ba76eb` |

**Probelauf der Serie** (`git merge-tree`, Cherry-pick in Mainline-Reihenfolge
auf die Branch-Spitze; bei einem Konflikt wird der Patch übersprungen, wie es
das stable-Tooling auch tut):

| # | Commit | 5.10 | 5.15 | 6.1 | 6.6 | 6.12 | 6.18 |
|---|---|---|---|---|---|---|---|
| 1 | `933bf0fcb325` | (n/a) | (n/a) | OK | OK | OK | OK |
| 2 | `962947b69589` | af_can.c, raw.c | af_can.c | af_can.c | af_can.c | af_can.c | af_can.c |
| 3 | `874f5f14cf62` | OK | OK | OK | OK | OK | OK |
| 4 | `0f3ad9ab40e3` | af_can.c, isotp.c, raw.c | af_can.c, isotp.c, raw.c | af_can.c, isotp.c, raw.c | af_can.c, isotp.c, raw.c | af_can.c, isotp.c, raw.c | af_can.c, isotp.c |
| 5 | `43c973a0887d` | raw.c | raw.c | raw.c | raw.c | raw.c | raw.c |
| 6 | `12297f855bbd` | OK | OK | OK | OK | OK | OK |
| 7 | `01b19ed9fa03` | OK | OK | OK | OK | OK | OK |

Damit sind die Mails reproduziert. Die Konflikte bei #4 und #5 sind teilweise
Folgekonflikte, weil im Probelauf #2 (bzw. #4) fehlt. Das tatsächliche
Konfliktbild ergibt sich erst, wenn #2 je Branch zurückportiert ist.

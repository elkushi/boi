# Бой

Two-player fighting game, played from two phones. Three rounds, two wins.
Punch, kick, block, jump. Single HTML file, no engine, no runtime dependencies.

## Netcode: attacker authority

A health-bar fighter over the internet normally feels terrible — you block,
and get hit anyway, because your block reached the other machine 150ms late.

This avoids that by letting **the attacker decide**. Each phone simulates only
its own fighter. When your attack's hitbox overlaps your opponent's last known
position, your phone resolves the hit and sends the result; their phone applies
the damage, knockback and stun it is told. So your own attacks always connect
when they look like they should, and never evaporate because of lag.

The cost is that blocking can occasionally register a frame late. That is
offset by giving every attack a visible wind-up (punch 100ms, kick 170ms)
rather than instant hits, so reactions are to animation rather than to frames.

## Moves

| | wind-up | damage | reach | knockback |
|---|---|---|---|---|
| punch | 100ms | 7 | 96 | low |
| kick | 170ms | 13 | 136 | high, pops up |

Blocking cuts damage to 20% and knockback to 35%, but only when facing the
attacker. You cannot block while attacking.

## Controls

`←` `→` move · `↑` jump · `J` punch · `K` kick · `L` block · `M` sound.
On phones: touch controls, landscape.

## Build

```bash
python3 build.py     # inlines sprites -> index.html
python3 serve.py     # preview on :8731
```

Online needs a Firebase Realtime Database config in `firebase.json`
(git-ignored). Rooms are stored under `rooms/F<code>` so they share one
database with the co-op game without colliding.

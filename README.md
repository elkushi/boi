# Бой — Мустафа против Алисы

Two-player fighting game for two phones in two cities. Best of three rounds,
75 seconds each. Single HTML file, no engine, no runtime dependencies except
Firebase Realtime Database for the room.

**Play:** https://elkushi.github.io/boi/ — one creates a room and sends the
link (or the 4-letter code), the other opens it. The fight starts by itself.
Without a partner: «Тренировка с ботом».

## What's in it

- **Fighters from the AI sprite sheets** (`raw/`): 36 poses each (idle, run,
  jump, fall, land, guard, hurt, jab, straight, heavy, kick, heavy kick,
  uppercut, air kick, energy blast, energy wave, charge, power-up, taunts,
  knockdown, get-up). `extract_poses.py` cuts them with pixel boxes and a
  colour-keyed flood fill (the background is dark and bluish; Moustafa's
  black shirt is not), scales every pose of a fighter by one factor and writes
  `sprites/poses/meta.json` with a per-pose horizontal anchor.
- **Chains:** УДАР → УДАР → УДАР = jab → straight → heavy punch, НОГА → НОГА =
  kick → heavy kick, but only if the previous hit landed. АПЕР launches.
  In the air: air kick / air punch.
- **Super meter** fills from hits given and taken, from a completed taunt
  (+25, but you are open while posing) and from holding СУПЕР (charging pose).
  Full meter + СУПЕР = energy blast projectile at range, energy wave up close.
  Two projectiles cancel each other.
- **Chaos** every 11–20 s, announced on screen: 🦆 a duck falls on someone,
  🍕 pizza heals whoever grabs it, 🌙 low gravity, 🍄 the losing fighter
  becomes a giant, ⚡ turbo speed.
- **Talking:** 😜 taunt with a random speech bubble per character, ❤️😂😡
  reactions that float over your fighter on both phones, round-end commentary
  lines, and a «Мир? ❤️» button after the match that fills both screens with
  hearts.
- Comic hit pops (БАМ, ХЛОП, ТРАХ!), hit-stop, screen shake, knockdowns with
  a get-up, a procedural bass beat (M mutes).

## Netcode: attacker authority

Each phone simulates only its own fighter and sends position, pose, HP and
meter 20 times a second. When your attack's hitbox overlaps the opponent's last
known position, *your* phone resolves the hit and sends the result; theirs
applies the damage, knockback and stun it is told. Your own attacks always
connect when they look like they should. The projectile works the same way:
its owner moves it and decides the hit, the other phone only draws it.

The host (room creator) is the authority for chaos spawns and for the time-up
result, so both phones see the same ducks and the same round winner. Rounds
end on either phone when it learns an HP is zero.

## Controls

Keyboard: `←` `→` move · `↑` jump · `J` punch · `K` kick · `U` uppercut ·
`L` block · `I` super / hold to charge · `T` taunt · `1` `2` `3` reactions ·
`M` mute. Phones: touch controls, landscape; 🔊 in the reaction row mutes.
Tapping a start button asks for fullscreen and locks landscape, so the browser
bar does not eat the buttons.

## Phones: why it is sized and drawn this way

`100vh` on mobile Chrome includes the hidden address bar, so a 16:9 box sized
by CSS alone overflows the screen and the bottom row of buttons disappears. The
stage is sized from `innerHeight` in JS instead. The canvas backing store is
the on-screen size (capped at 1920 px wide), not a fixed 2560×1440; the arena is
pre-rendered once into an offscreen canvas; emoji and projectile gradients are
cached; sprites are `ImageBitmap`s; and `ctx.filter` is never used, because it
drops Android Chrome's canvas to software rendering.

## Build

```bash
/usr/bin/python3 extract_poses.py   # raw/*.png -> sprites/poses/ (needs Pillow + numpy)
/usr/bin/python3 build.py           # inlines sprites + arena + firebase.json -> index.html
/usr/bin/python3 serve.py           # preview on :8731
./deploy.sh "message"               # build, commit, push to elkushi/boi (GitHub Pages)
```

Online needs a Firebase Realtime Database config in `firebase.json`
(git-ignored). Rooms live under `rooms/F<code>` and are removed when the host
disconnects. `raw/` (the sprite sheets) stays out of git; the built
`index.html` carries everything.

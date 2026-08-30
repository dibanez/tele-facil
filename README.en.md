*[Español](README.md) · **English***

# Tele Fácil

Run the television from a panel of big buttons — on a tablet, a phone or any
screen — instead of the set-top box remote: six channels, volume, and little
else. It runs on **Home Assistant** on a Raspberry Pi.

It was built so that an elderly person could watch TV without fighting a
forty-button remote. Whoever uses it never needs to know there is anything
behind it.

📺 **[Read the write-up: "Solo quiere ver la tele"](https://dibanez.github.io/tele-facil/)** —
the problem it solves, what it took to build, and what adding voice would cost.
*(In Spanish.)*

```
Button panel  →  Home Assistant  →  Android TV Remote  →  Set-top box  →  TV
                                 └→  ADB (for the one thing the remote can't do)
```

<p align="center">
  <img src="docs/img/panel.jpg" width="300"
       alt="The panel on a phone screen: six large numbered buttons with channel names, and a volume row with down, mute and up.">
</p>
<p align="center"><em>This is everything the person using it sees.</em></p>

> **A note on language.** The code, comments and step-by-step guides under
> `docs/` are in Spanish, as are the channel names — the project targets Spanish
> DTT and a Spanish-speaking household. This README covers everything you need
> to understand, evaluate and port the project.

## Supported set-top boxes

| Set-top box | Status |
|---|---|
| **DIGI R2A** | Verified end to end against real hardware on 2026-08-19: volume, mute, navigation and switching to the six main channels all work |

Only one so far. The project is split into layers precisely so that adding
another does not mean rewriting it: see [Porting to another
box](#porting-to-another-box). The measured details — timings, keys the box
ignores — are in [How channel switching works](#how-channel-switching-works)
and in [Known limitations](#known-limitations).

## What you need

| Piece | Notes |
|---|---|
| A **supported set-top box** | Powered on and on the same network as the Pi. Today, the DIGI R2A |
| **Raspberry Pi** running Home Assistant | Tested on HA OS; needs **HA 2024.8 or newer** for the `action:` syntax |
| **Android TV Remote** integration | The primary path: paired once with an on-screen code, survives reboots and reconnects on its own |
| **Android Debug Bridge** integration | Only to fire the `digitv://channel` deep link — the one thing the Google TV remote protocol cannot do |
| A network without client isolation | Plus DHCP reservations by MAC for the Pi and the box |

## Installation

The full procedure, with a verification step at each phase, is in
**[docs/01-despliegue.md](docs/01-despliegue.md)** (Spanish). In short:

**1. Check the box is reachable and see which control path it offers.** With the
box powered on and showing a picture, from the Pi or any machine on the same
network:

```bash
python3 tools/probe_deco.py
```

No dependencies: it discovers over mDNS, sweeps the subnet and reports whether
Android TV Remote (recommended), ADB, or only a sign of life is available.

**2. Pair the integrations.** In Home Assistant, *Settings → Devices & Services
→ Add Integration*: **Android TV Remote** with the box's IP (a code appears on
the TV), and **Android Debug Bridge** pointed at `<box-ip>:5555`.

> On the R2A, ADB is *not* enabled the classic way — tapping "Build number"
> seven times does nothing. You have to install a *Developer Tools* app from
> Google Play and turn on network debugging from there.

**3. Copy the configuration.**

```bash
cp homeassistant/packages/tele_facil.yaml <config>/packages/
```

Then add the `packages:` line from
[`homeassistant/configuration.snippet.yaml`](homeassistant/configuration.snippet.yaml)
to your `configuration.yaml` and restart Home Assistant.

**4. Adjust the values for your setup** (see the table below) and build the
panel from [`homeassistant/dashboards/tv.yaml`](homeassistant/dashboards/tv.yaml):
*Settings → Dashboards → Add dashboard → Edit in YAML*, then paste the contents.

### Values you must change

No real IP addresses are committed to this repository. These three values are
placeholders:

| Where | Key | What to put |
|---|---|---|
| `homeassistant/packages/tele_facil.yaml` | `target_remote` | The `entity_id` created by Android TV Remote, usually `remote.digi_r2a` |
| `homeassistant/packages/tele_facil.yaml` and `dashboards/tv.yaml` | `media_player.android_tv_192_168_1_20` | The ADB entity — Home Assistant names it after the box's IP, with underscores |
| `homeassistant/configuration.snippet.yaml` | `host_ip` / `advertise_ip` | The Pi's static IP |

Every occurrence is flagged with a `# CAMBIAR` ("change me") comment.

## How it is organised

```
tools/probe_deco.py                       Network probe: finds the box and says
                                          which control path it supports
homeassistant/packages/tele_facil.yaml    The control scripts (the core)
homeassistant/dashboards/tv.yaml          The big-button panel
homeassistant/configuration.snippet.yaml  Blocks for configuration.yaml
docs/                                     Deployment, maintenance, remote access
```

The scripts sit in three layers, and that separation is the only thing that
makes supporting more than one box realistic:

| Layer | Script | What it knows |
|---|---|---|
| 1 | `tv_send_key` | **How the box is reached.** The only script that touches hardware: it sends one key over Android TV Remote and, if the entity is `unavailable` (box rebooted, Wi-Fi blipped), reloads the integration and waits for it to come back before giving up. Moving to ADB, or to an infrared blaster, means editing this script and nothing else |
| 2 | `tv_canal` | **How a channel is reached.** The model-specific part: this is the DIGI R2A implementation |
| 3 | `tv_la1`, `tv_volumen_mas`… | **What the person asks for.** One action per thing. This is what the panel buttons call, and the layer that should never change |

## How channel switching works

This is the part that was hard, and the reason this project exists instead of
being four lines of YAML.

**The R2A does not accept numeric input.** Sending `2` does not change channel,
not even followed by `OK`. Digits go to the box firmware, not to the
`ro.digionline.tv` app running on top of it, and on the live screen they do
nothing at all. `KEYCODE_CHANNEL_UP` / `DOWN` and the arrow keys are ignored
too.

The only path that works is navigating the app's channel grid:

```
digitv://channel deep link  →  wait 6 s  →  N right presses  →  OK  →  wait 5 s  →  OK
```

Four details make this reliable rather than a house of cards:

1. **The `digitv://channel` link always leaves focus on position 1**, wherever
   the box happened to be (guide open, programme page, settings). It is a fixed
   starting point, so counting positions is absolute and every command
   self-corrects.
2. **On the programme page, "Ver ahora" (Watch now) is already focused.**
   Sending `DOWN` before `OK` moves focus to the "Similar" row and you end up
   watching something else entirely.
3. **Key presses go one at a time, ~0.8 s apart.** With `num_repeats` the
   integration fires them too fast and focus escapes into the side menu.
4. **`androidtv.adb_command` truncates anything over ~9 s** and still returns
   HTTP 200 — the failure is silent. That is why every wait lives in a Home
   Assistant `delay:` and never inside the command.

The script runs in `mode: restart`: on a touch panel it is easy to tap two
channels in a row, and with a queue the second would wait 20 s while the TV
visits a channel nobody asked for. Since every sequence starts from the fixed
point, cutting one short leaves nothing broken.

## Porting to another box

Layer 3 — what the person asks for — is the same for any box: "put Telecinco
on" means the same thing on an R2A as on a Movistar Plus+. What changes is how
it gets done. So porting the project is, in principle:

1. **Layer 1:** if the box is Android TV, `tv_send_key` works as is and you only
   point `target_remote` at the new entity. If it is not (proprietary Linux,
   infrared only), you rewrite that one script.
2. **Layer 2:** rewrite `tv_canal`. This is the real work, and it has to be
   measured against the hardware: which keys it ignores, how long each screen
   takes to paint, whether there is a fixed starting point to count from.
3. **Layer 3:** adjust the channel positions, and nothing else.

The trick that made the R2A work — find an action that always leaves the
interface in the same place, then count from there instead of assuming where it
was — will probably transfer to other boxes. The section above describes how it
was found, which is the most reusable thing in this repository.

## Known limitations

- **A channel change takes 12-18 seconds.** The grid has to be navigated; there
  is no shortcut. Volume and navigation are instant.
- **Position 1 is "La 1 Galicia"**, the regional feed, not the national one.
- **Programme names do not identify the channel** — they change with the hour.
  To check what is playing, press `UP` during playback and read the info bar.
- **If the operator reorders the grid, positions must be adjusted.** Edit the
  `posicion:` value of the affected channel script, nothing else.
- **ADB disables itself after a reboot on many Android TVs.** That is why the
  Google TV remote protocol is the primary path and ADB is reduced to the deep
  link.

## Troubleshooting

From the outside in; each step rules out one layer:

1. Does `http://<pi-ip>:8123/` load? → if not, the Pi is off or off the network.
2. Is the `remote.*` entity `unavailable`? → box powered off, or its IP changed.
3. Does `python3 tools/probe_deco.py` find the box? → if not, a network problem
   or the pairing was lost.

Common failures and routine maintenance are covered in
[docs/03-mantenimiento.md](docs/03-mantenimiento.md).

## Documentation

| Document | Contents |
|---|---|
| [Solo quiere ver la tele](https://dibanez.github.io/tele-facil/) | The project write-up: the underlying problem, the design decisions, and the two routes to voice control |
| [docs/01-despliegue.md](docs/01-despliegue.md) | Phase-by-phase installation, with a check at each step |
| [docs/03-mantenimiento.md](docs/03-mantenimiento.md) | Troubleshooting and maintenance |
| [docs/04-tailscale.md](docs/04-tailscale.md) | Remote access for support without opening router ports |

## Licence

[MIT](LICENSE).

A personal project, unaffiliated with DIGI or any other operator. Operator and
channel names are trademarks of their respective owners.

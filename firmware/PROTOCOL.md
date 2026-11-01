# rondOfeed protocol

One text line per message, ending with `\n`. The same commands work over USB serial and over BLE.

## Transports

- **USB serial:** the Pico shows up as a serial port (for example `/dev/ttyACM0`), 115200 8N1 is fine, the speed does not matter. USB is trusted, no login is needed.
- **BLE:** the Pico advertises as `rondOfeed` (category Domestic Appliance) with a service `7a1c0001-5a3e-4c6b-9d21-0f3c2a8e0001`. Write command lines to the characteristic `…0002`, read answers and events as notifications of `…0003`. A line may be split over several packets, so collect the bytes until `\n`. A BLE client has to send `AUTH <token>` first, see below. The standard Device Information Service (`0x180A`) tells manufacturer, model and firmware version, so apps can recognise the device.

## Messages

A command may start with an id `@<id>`, which the answer repeats, so an app can match answers to requests:

```
@7 FEED 2
@7 OK accepted 2
EVENT fed 1 beams=3
EVENT fed 2 beams=1
EVENT done fed=2 missed=0
```

Answers start with `OK` or `ERR <code> <text>`. Lines starting with `EVENT` can arrive at any time and go to every connected client.

## Commands

| Command | Answer | Notes |
|---|---|---|
| `PING` | `OK pong` | |
| `VERSION` | `OK fw=0.1 proto=1` | |
| `AUTH <token>` | `OK` | BLE only, until the connection ends |
| `STATUS` | `OK k=3 portions=47 remaining=44 busy=0 state=ok last=fed` | `state=uncertain` after a power loss during a move |
| `FEED [n]` | `OK accepted <n>` | n from 1 to 10, one position per portion, the light barrier confirms each one |
| `STOP` | `OK` | no further portion after the current one |
| `ZERO` | `OK` | the disc is closed at the outlet now, sets position 0 and clears `uncertain` |
| `JOG <steps>` | `OK` | maintenance, signed microsteps (±800), to align the disc by hand, then `ZERO` |
| `DISC <portions>` | `OK` | 47, 59 or 69 for the three discs, then `ZERO` |
| `SETTOKEN <token>` | `OK` | USB only, sets the BLE token |

## Events

| Event | Meaning |
|---|---|
| `EVENT fed <i> beams=<c>` | portion `i` of the request came through, `c` interruptions of the light barrier |
| `EVENT no_portion <i>` | nothing passed the light barrier in time |
| `EVENT done fed=<a> missed=<b>` | the request is finished |
| `EVENT error <code>` | the request was stopped, for example `empty` |

## Errors

| Code | Meaning |
|---|---|
| `syntax` | unknown command or bad argument |
| `auth` | BLE client has not sent the right token |
| `busy` | a feed is running |
| `limit` | too many portions per request, per hour or too soon after the last one |
| `empty` | no portion left on the disc, load it and send `ZERO` |
| `uncertain` | the position is not known, align the disc and send `ZERO` |

## Rules

- A feed moves the disc by one position per portion and then waits for the light barrier. If nothing arrives it reports `no_portion` and goes on with the next portion. Later the firmware can try more positions, see `RETRY_EXTRA` in `config.py`.
- The motor driver is only on during a move.
- The position is written to flash before and after each move. If the power fails in between, `state=uncertain` blocks feeding until `ZERO`.
- BLE needs the token from `SETTOKEN`. Without a token BLE accepts only `PING` and `VERSION`. The BLE link itself is not protected against someone in range who sniffs the token, so treat this as a protection against accidents.

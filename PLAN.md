# rondOfeed plan

Notes for the next steps. Dimensions, printing and assembly are in the [README](README.md).

## Electronics


- **Controller:** Raspberry Pi Pico W or Pico 2 W. Same form factor as the Pico, so the carrier and USB cutout stay as they are.
- **Driver:** Adafruit TMC2209 Breakout (ADA6121). Motor 5–29 V, logic 3–5 V, up to 2 A, screw terminals, 22 µF electrolytic capacitor on the board.
- **Power:** 12 V from the power supply to the breakout, 12 V to 5 V converter through a Schottky diode to `VSYS` on the Pico. See [wiring.svg](wiring.svg).

### Wiring (proposal)

| Pico | Breakout / part |
|---|---|
| GP2 | `STEP` |
| GP3 | `DIR` |
| GP4 | `EN`, plus 10 kΩ to 3V3 |
| GP5 | `DIAG` |
| GP6 | Break-beam sensor |
| VSYS | 5 V from the converter through Schottky diode 1N5819 |
| 3V3 | `VDD`, `MS1`, `MS2` (high = 1/16 microstep, the default would be 1/8) |
| GND | Common ground with power supply, converter and breakout |

### Rules for a reliable build

- Add an electrolytic capacitor of 100–470 µF, at least 25 V, directly on the breakout's 12 V terminals.
- Never connect or disconnect the motor while powered.
- The 10 kΩ pull-up keeps the motor unpowered while the Pico boots.
- Set the motor current on the potentiometer before any longer test. Exact motor model is not chosen yet, placeholder 1.0 A.
- Short, secure wires, no jumper wires.
- Prototyping board: Adafruit Perma-Proto Quarter-Size (43.2 × 50.8 mm), layout in [wiring_layout.svg](wiring_layout.svg). Its 2 mounting holes are 35.6 mm apart on the short axis, so it sits with the long side across the carrier (along X). The `DUMMY_Perfboard` body in the model is drawn 55 × 44 mm, a little larger than the board.
- The converter model is not chosen yet. The layout assumes a 3-pin in-line module of 11.5 × 7.5 mm.

## Firmware (Pico W and Pico 2 W)

MicroPython, in [firmware/](firmware/README.md). Commands over USB serial and BLE, no Wi-Fi for now. The protocol is in [firmware/PROTOCOL.md](firmware/PROTOCOL.md). The core is tested on a PC, the rest on a Pico W without motor, driver and light barrier. The motor and the light barrier have not run yet.

Decisions:

- The touchscreen app runs on Linux and uses plain USB serial. BLE is for phones, tablets and computers.
- Every feed is confirmed by the light barrier. If no portion comes, the firmware reports it. Later it may keep trying (`RETRY_EXTRA`).
- Limits per request, per hour and between requests apply to every source.

### Firmware: still to do

The firmware stays as it is for now. Only a Pico W is available, so nothing with the motor has been tried. Open points, roughly in the order to do them:

**Needs the hardware**

1. Wire the TMC2209, motor, light barrier and the 10 kΩ pull-up on `EN`, as in [wiring.svg](wiring.svg). Check that `EN` reads high at boot, so the driver stays off.
2. Check the motor: send `JOG 20` and `JOG -20`, flip `DIR_FORWARD` in `firmware/config.py` if it turns the wrong way, then set the motor current on the driver.
3. Check `BEAM_BROKEN_LEVEL` against the real sensor. If it is wrong, every portion reports `no_portion`.
4. Tune `STEP_RATE_MIN`, `STEP_RATE_MAX` and the ramp with the real disc. The disc is heavy, so the values are guesses. Look for lost steps.
5. Align the disc, send `ZERO`, then `FEED` and see if the portion lands in the chute. Check that each hole is cleanly over the outlet and that the disc stays put when the driver is off (see Position).
6. Run the three discs (`DISC 47`, `DISC 59`, `DISC 69`) and check that the positions add up to a full turn.
7. Test a real power loss in the middle of a move: the next start must report `state=uncertain`. Cutting off the program with Ctrl-C in the middle of a move already does this on the bench.
8. Run it for hours and check the motor and driver temperature, see "After assembly".

**Can be done now**

- Copy the firmware to the board with one script instead of by hand (including the `aioble` library and the `WATCHDOG_MS` setting).
- Test BLE with a phone or tablet, not only from a PC. Check the pairing, the 20 byte packets with a small MTU and what the app has to do (login, collect lines until `\n`).
- Decide on BLE security. The token travels unencrypted. Bonding with encryption would protect against someone listening in, but without a display or button there is no pairing passkey. A pairing button on a free pin would help.
- Before the device goes into use, make it safe against a stray Ctrl-C on USB. MicroPython stops the program when the byte `0x03` arrives on the serial port, from any program that writes to it, and a feed in the middle stays unfinished (the position is `uncertain` after that). Two measures, both off during development:
  - Switch Ctrl-C off with `micropython.kbd_intr(-1)`, so `0x03` is an ordinary character that the parser ignores. Put it behind a flag in `config.py`. With it on, `mpremote` can no longer stop the program, so to update the board it has to be reset or the file removed.
  - Turn the watchdog on (`WATCHDOG_MS = 8000` in the repository, it is off on the board for now). It cannot be stopped once started, so the board restarts by itself about 8 seconds after the program has stopped.
- Make `STOP` work in the middle of a move. It only ends after the current portion now.
- Let the firmware keep trying: when no portion comes, move on to the next position until one comes, with an upper limit. `RETRY_EXTRA` is the hook for it.
- A reference for the disc position, for example a magnet and a Hall sensor on the disc, so a power loss does not need a manual `ZERO`.
- Show the state on the board LED (idle, moving, error, BLE connected).
- Let the app send the time, if schedules should be checked on the device. There is no clock on the Pico.
- Move the firmware to C if MicroPython turns out too slow or too big. The protocol would stay the same.
- Write the tests for `motor.py`, `beam.py`, `usb_serial.py` and `ble.py`, which only run on a board (for example a test script that talks to the board over USB).

### Power the motor only when feeding

Only the power supply has ventilation slots (floor and front right wall), so the motor must not produce continuous heat.

- The motor is only powered when a feed is about to happen.
- After each feeding step it is unpowered again.
- Sequence: enable the driver (`EN` low), wait briefly, move one position, wait briefly, disable the driver (`EN` high).
- Safety shutdown: the driver also turns off after errors and after a timeout.
- At startup the driver stays off until the firmware deliberately enables it.

### Position

- Position 0 is closed, each further position releases one portion. The firmware must support all discs: 47 portions at 7.5°, 59 at 6° or 69 at 5.14°.
- Motor: 0.9° NEMA 17, so 6400 microsteps per turn at 1/16. Per position: 133.33, 106.67 or 91.43. Accumulate the target position and round that, rather than rounding each step.
- Unpowered, only the motor's detent torque holds the disc. The motor settles on the nearest full step (up to 0.45°, about 0.7 mm at the outer hole ring). Portion positions are mostly not on full steps.
- To check: is the hole still cleanly over the outlet after re-enabling, and does the disc stay put when unpowered?
- The current position must survive a restart, or there must be a homing move. There is no sensor for this yet.

### Break-beam sensor

- Counts each dispensed portion in the chute.
- If no portion arrives after a step, this is reported.

## Before printing

- Choose the IEC inlet, and check the `IEC_CUT` cutout and the 3 mm wall thickness.
- Check the break-beam sensor `IR_D` and threaded insert `INSERT_D` on the real parts.
- Measure the food and set `HOLE_D`. Pieces under about 8 mm can fall through to the neighbouring hole.
- Print a test piece: disc centre with shaft and set screw, plus the motor block.
- Plan the wiring with the real parts, as there is little room next to the power supply and carrier.
- Bowl: at most about 57 mm high.

## After assembly

- Run a continuous test in normal operation for several hours and measure the internal temperature at the power supply. PETG softens at about 70 °C. The power supply loses output above 50 °C.
- If it gets too warm or damp: add slots to the rear or side wall.
- Mains wiring only by someone qualified to do it safely.
- Test cleaning: the lid, disc and plate have to come off to reach the chute.

## Open decisions

- Chute at 40° or 45°? 45° prints more easily, but the bowl would have to be lower.
- Chamfer the top of the IEC and USB cutouts? They currently have horizontal bridges.

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
| GP6 | Light barrier: collector of the phototransistor, plus 10 kΩ to 3V3 |
| VSYS | 5 V from the converter through Schottky diode 1N5819 |
| 3V3 | `VDD`, `MS1`, `MS2` (high = 1/16 microstep, the default would be 1/8) |
| GND | Common ground with power supply, converter and breakout |

### Rules for a reliable build

- Add an electrolytic capacitor of 100–470 µF, at least 25 V, directly on the breakout's 12 V terminals.
- Never connect or disconnect the motor while powered.
- The 10 kΩ pull-up keeps the motor unpowered while the Pico boots.
- Set the motor current on the potentiometer before any longer test. Exact motor model is not chosen yet, placeholder 1.0 A.
- Short, secure wires, no jumper wires.
- Prototyping board, half size, lengthwise (along Y) on the carrier, left of the motor and in front of the Pico. Layout in [wiring_layout.svg](wiring_layout.svg), drawn for the Adafruit board.
  - Adafruit Perma-Proto Half-Size (81 × 51 mm, ADA1609): 2 mounting holes 73.7 mm apart on the long axis, in the middle of the short sides.
  - GeeekPi Half-Size: 4 corner holes Ø3 mm, 55 × 85 mm apart (centre to centre). Drill them to 3.2 mm for the M3 screws. Its outline is not known yet, the model assumes 62 × 92 mm (`DUMMY_Perfboard`).
  - The carrier has posts for both boards (`PERF_HOLE_DY`, `GEEK_HOLES`). The two Adafruit posts end up under the GeeekPi board. If they touch a solder joint there, file them down.
  - The carrier has tabs on the left and at the front, so that all 4 carrier screws stay clear of both boards.
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
- Built from two single 5 mm parts, because ready-made break-beam modules (for example Adafruit ADA2168, 20 × 10 × 8 mm) do not fit the Ø5.2 mm holes in the chute.
- Emitter: IR LED 5 mm, 940 nm (Vishay TSAL6200). 3V3 → 100 Ω → anode, cathode to GND, about 20 mA.
- Receiver: IR phototransistor 5 mm with daylight filter (Osram SFH 300 FA or Everlight PT334-6C). Collector to GP6 with 10 kΩ to 3V3, emitter to GND. The chute is open at the outlet, so the filter helps against room light.
- The beam crosses about 25–30 mm (24 mm inside plus the walls). A simple unmodulated barrier is enough for this.
- GP6 is low while the beam is seen and high when it is broken, so `BEAM_BROKEN_LEVEL = 1`. Check on the real build.
- The holes are 8 mm above the bottom of the tube, so even small pieces cross the beam.

### Mains inlet (Europe, 230 V)

- IEC C14 inlet as a 3-in-1 module: inlet, 2-pole rocker switch and 5 × 20 mm fuse drawer, snap-in. Cutout `IEC_CUT` = 28 × 47 mm (width × height), about 31 mm deep inside the housing (`DUMMY_IEC` is 30 mm).
- Fuse T1A (slow-blow), 250 V. The power supply draws well under 1 A at 230 V, but has a high inrush current when switched on, so use a slow-blow fuse. These modules often come with 10 A, which is far too much.
- Snap-in clips are often made for 1–2 mm panels. The 3 mm rear wall has a pocket on the inside, so it is only `IEC_WALL` = 2 mm thick for 7 mm around the cutout (`IEC_RIM`). The outside stays flat.
- Connect protective earth from the inlet to terminal FG on the power supply.

## Before printing

- Check the chosen IEC inlet against the `IEC_CUT` cutout and the panel range of its clips (`IEC_WALL`, 2 mm), see Mains inlet.
- Check `IR_D` with the real IR LED and phototransistor, and the threaded insert `INSERT_D`.
- Measure the food and set `HOLE_D`. Pieces under about 8 mm can fall through to the neighbouring hole.
- Print a test piece: disc centre with shaft and set screw, plus the motor block.
- Plan the wiring with the real parts, as there is little room next to the power supply and carrier.
- Measure the hole spacing of the board before printing the carrier: Adafruit 73.7 mm, GeeekPi 55 × 85 mm. For the GeeekPi board also check the outline (assumed 62 × 92 mm) and that the rows and rails match the wiring layout.
- Bowl: at most about 70 mm high with `Chute.stl`, but it has to stand right against the wall. With `Chute_long.stl` at most about 57 mm.

## After assembly

- Run a continuous test in normal operation for several hours and measure the internal temperature at the power supply. PETG softens at about 70 °C. The power supply loses output above 50 °C.
- If it gets too warm or damp: add slots to the rear or side wall.
- Mains wiring only by someone qualified to do it safely.
- Test cleaning: the lid, disc and plate have to come off to reach the chute.

## Open decisions

- Chute at 40° or 45°? 45° prints more easily, but the bowl would have to be lower.
- Chamfer the top of the IEC and USB cutouts? They currently have horizontal bridges.

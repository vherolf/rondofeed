# rondOfeed plan

Notes for the next steps. Dimensions, printing and assembly are in the [README](README.md).

## Electronics


- **Controller:** Raspberry Pi Pico 2 W. Same form factor as the Pico, so the carrier and USB cutout stay as they are.
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

## Firmware (Pico 2 W)

Not written yet.

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

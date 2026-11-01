# rondOfeed firmware

MicroPython for the Raspberry Pi Pico W and Pico 2 W. It moves the disc one position per portion, checks every portion with the light barrier and takes commands over USB serial and BLE. The commands are in [PROTOCOL.md](PROTOCOL.md).

**Status:** the core (`feeder.py`, `protocol.py`, `motor_plan.py`, `store.py`) is tested on a PC. On a Pico W with MicroPython 1.29.0 these work, tested **without a motor, driver or light barrier**: USB serial, BLE (login, commands, long lines, readable names and the Device Information Service in nRF Connect), the whole feed sequence including `no_portion`, the step pulses (the duration of a move matches the plan) and `state=uncertain` after a move that is cut off. The motor itself and the light barrier have **not run yet**.

## Files

| File | Job |
|---|---|
| `config.py` | pins, speeds, limits, BLE UUIDs, all in one place |
| `feeder.py` | position, limits, feed sequence, light barrier check |
| `protocol.py` | understands command lines, same for USB and BLE |
| `motor_plan.py` | speed ramp for one move |
| `store.py` | position, disc and BLE token in flash |
| `motor.py` | step pulses from the PIO, driver on only during a move |
| `beam.py` | light barrier counter |
| `usb_serial.py`, `ble.py` | the two ways to send commands |
| `main.py` | starts everything |

## Install

1. Flash MicroPython onto the Pico: hold BOOTSEL while plugging in USB and copy the UF2 for your board from micropython.org (the `RPI_PICO_W` or `RPI_PICO2_W` build).
2. Copy the files to the board, for example with [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html):

   ```sh
   cd firmware
   mpremote cp config.py motor_plan.py store.py feeder.py protocol.py motor.py beam.py usb_serial.py ble.py main.py :
   ```
3. BLE needs the `aioble` library: `mpremote mip install aioble`.
4. Reset the board. `main.py` starts by itself.

While you are developing, set `WATCHDOG_MS = 0` in `config.py`, otherwise the board resets when you stop the program from the REPL.

## First start

1. Try the protocol on the bench first, without the housing: Pico, TMC2209, motor and 12 V.
2. Open the serial port with a terminal (`picocom /dev/ttyACM0` or `screen /dev/ttyACM0 115200`) and send `PING`, then `STATUS`.
3. Check the direction with `JOG 50` and `JOG -50`. If it turns the wrong way, flip `DIR_FORWARD` in `config.py`.
4. Align the disc so that a closed part is over the outlet and send `ZERO`. Then `FEED`.
5. Check `BEAM_BROKEN_LEVEL` in `config.py` against your sensor, or every portion reports `no_portion`.
6. Set a token for BLE over USB: `SETTOKEN <token>`.

From a Linux program, USB serial is plain `pyserial`:

```python
import serial
port = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
port.write(b"@1 FEED 1\n")
while True:
    print(port.readline().decode().strip())   # @1 OK accepted 1, then EVENT fed 1 ...
```

## Tests

On a PC, with plain Python:

```sh
cd firmware/tests
python3 -m unittest discover -v
```

The tests use a fake motor and a fake light barrier, so they run without a board.

## Not done yet

- Stopping in the middle of a move. `STOP` ends after the current portion.
- A reference sensor for the disc position. After a power loss in the middle of a move the position is `uncertain` until `ZERO`.
- Trying more positions when no portion comes (`RETRY_EXTRA` is the hook for it).
- Speeds and ramp are guesses. Tune them with the real disc.

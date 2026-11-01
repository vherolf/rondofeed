"""rondOfeed: Start auf dem Pico W / Pico 2 W mit MicroPython."""
import asyncio

import config
from beam import Beam
from feeder import Feeder
from motor import Motor
from protocol import Dispatcher
from store import Store
from usb_serial import UsbSerial


def main():
    motor = Motor()    # zuerst, damit EN sofort high ist
    store = Store(default_portions=config.DEFAULT_PORTIONS)
    feeder = Feeder(motor, Beam(), store, config)
    transports = []

    def emit(line):
        for t in transports:
            t.send(line)

    dispatcher = Dispatcher(feeder, store, config, emit)
    usb = UsbSerial(dispatcher)
    transports.append(usb)
    tasks = [usb.run()]
    try:
        from ble import Ble
        ble = Ble(dispatcher)
        transports.append(ble)
        tasks.append(ble.run())
    except ImportError:
        pass   # MicroPython ohne Bluetooth, USB geht trotzdem

    if config.WATCHDOG_MS:
        from machine import WDT
        wdt = WDT(timeout=config.WATCHDOG_MS)

        async def keep_alive():
            while True:
                wdt.feed()
                await asyncio.sleep(1)

        tasks.append(keep_alive())

    async def run_all():
        await asyncio.gather(*tasks)

    asyncio.run(run_all())


main()

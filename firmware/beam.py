"""Lichtschranke im Auslauf: zaehlt Unterbrechungen, entprellt."""
import asyncio
import time

from machine import Pin

import config


class Beam:
    def __init__(self):
        self.count = 0
        self._last = time.ticks_ms()
        self.pin = Pin(config.PIN_BEAM, Pin.IN, Pin.PULL_UP)
        self.pin.irq(self._irq, Pin.IRQ_FALLING | Pin.IRQ_RISING)

    def _irq(self, pin):
        if pin.value() == config.BEAM_BROKEN_LEVEL:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last) > config.BEAM_DEBOUNCE_MS:
                self.count += 1
                self._last = now

    def clear(self):
        self.count = 0

    async def wait(self, timeout_ms):
        """Wartet auf die erste Unterbrechung. Gibt True zurueck, wenn eine kam."""
        start = time.ticks_ms()
        while self.count == 0:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return False
            await asyncio.sleep_ms(5)
        return True

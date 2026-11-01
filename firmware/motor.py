"""Schrittmotor ueber den TMC2209: Impulse kommen aus der PIO, damit USB und BLE das Timing nicht stoeren."""
import asyncio

import rp2
from machine import Pin

import config
import motor_plan


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def _pulses():
    wrap_target()
    pull(block)            # Anzahl Impulse minus 1
    mov(x, osr)
    label("step")
    set(pins, 1)[7]
    set(pins, 0)[6]
    jmp(x_dec, "step")     # 16 Takte je Schritt
    push(block)            # Fahrstueck fertig
    wrap()


_CYCLES_PER_STEP = 16


class Motor:
    def __init__(self):
        self.en = Pin(config.PIN_EN, Pin.OUT, value=1)   # Treiber aus
        self.dir = Pin(config.PIN_DIR, Pin.OUT, value=0)
        self.step = Pin(config.PIN_STEP, Pin.OUT, value=0)
        self.sm = rp2.StateMachine(0, _pulses, freq=config.STEP_RATE_MIN * _CYCLES_PER_STEP, set_base=self.step)

    async def move(self, steps):
        """Faehrt `steps` Mikroschritte, negativ ist rueckwaerts. Der Treiber ist nur waehrend der Fahrt an."""
        forward = config.DIR_FORWARD if steps >= 0 else 1 - config.DIR_FORWARD
        plan = motor_plan.segments(abs(steps), config.STEP_RATE_MIN, config.STEP_RATE_MAX,
                                   config.RAMP_STEPS, config.RAMP_SECTIONS)
        self.dir.value(forward)
        self.en.value(0)
        try:
            await asyncio.sleep_ms(config.ENABLE_SETTLE_MS)
            for count, rate in plan:
                # die Taktrate aendert man nur mit init, das setzt die State Machine auf den Anfang zurueck
                self.sm.init(_pulses, freq=rate * _CYCLES_PER_STEP, set_base=self.step)
                self.sm.active(1)
                self.sm.put(count - 1)
                while self.sm.rx_fifo() == 0:
                    await asyncio.sleep_ms(2)
                self.sm.get()
                self.sm.active(0)
        finally:
            self.sm.active(0)
            await asyncio.sleep_ms(config.DISABLE_DELAY_MS)
            self.en.value(1)

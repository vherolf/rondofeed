"""BLE: ein Dienst mit einer Schreib-Eigenschaft fuer Befehle und einer Benachrichtigung fuer Antworten."""
import asyncio

import aioble
import bluetooth

import config
from protocol import Session

_CHUNK = 20   # Standard-MTU 23 minus 3 Byte Kopf


class Ble:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        service = aioble.Service(bluetooth.UUID(config.BLE_SERVICE))
        self.rx = aioble.Characteristic(service, bluetooth.UUID(config.BLE_RX), write=True, capture=True)
        self.tx = aioble.Characteristic(service, bluetooth.UUID(config.BLE_TX), read=True, notify=True)
        # Lesbare Namen in Tools wie nRF Connect (Characteristic User Description, 0x2901)
        aioble.Descriptor(self.rx, bluetooth.UUID(0x2901), read=True, initial=b"rondOfeed commands")
        aioble.Descriptor(self.tx, bluetooth.UUID(0x2901), read=True, initial=b"rondOfeed answers")
        aioble.register_services(service)
        # Standard sind 20 Byte, laengere Befehle wie AUTH mit Token kaemen sonst abgeschnitten an
        bluetooth.BLE().gatts_set_buffer(self.rx._value_handle, 128, True)
        self.connection = None

    def send(self, line):
        """Ereignisse an den verbundenen Client, in Stuecken zu 20 Byte."""
        if self.connection is None:
            return
        data = (line + "\n").encode()
        try:
            for i in range(0, len(data), _CHUNK):
                self.tx.notify(self.connection, data[i:i + _CHUNK])
        except Exception:
            pass

    async def _session(self, connection):
        session = Session(trusted=False)
        buf = b""
        while connection.is_connected():
            try:
                _, data = await self.rx.written(timeout_ms=1000)
            except asyncio.TimeoutError:
                continue
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode().strip()
                if text:
                    self.send(self.dispatcher.handle(text, session))
            if len(buf) > 120:
                buf = b""

    async def run(self):
        while True:
            async with await aioble.advertise(250000, name=config.BLE_NAME,
                                              services=[bluetooth.UUID(config.BLE_SERVICE)]) as connection:
                self.connection = connection
                try:
                    await self._session(connection)
                finally:
                    self.connection = None

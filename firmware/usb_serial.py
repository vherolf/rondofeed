"""USB-Seriell: Befehlszeilen von stdin lesen, Antworten und Ereignisse nach stdout schreiben."""
import asyncio
import select
import sys

from protocol import Session


class UsbSerial:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.session = Session(trusted=True)

    def send(self, line):
        sys.stdout.write(line + "\n")

    async def run(self):
        poll = select.poll()
        poll.register(sys.stdin, select.POLLIN)
        buf = ""
        while True:
            while poll.poll(0):
                ch = sys.stdin.read(1)
                if ch in ("\n", "\r"):
                    if buf.strip():
                        self.send(self.dispatcher.handle(buf, self.session))
                    buf = ""
                elif len(buf) < 120:
                    buf += ch
            await asyncio.sleep_ms(5)

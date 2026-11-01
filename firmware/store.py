"""Zustand im Flash: Position, Scheibe und BLE-Token. Wird vor und nach jeder Fahrt geschrieben."""
import json
import os


class Store:
    DEFAULTS = {"k": 0, "portions": 47, "dirty": False, "token": ""}

    def __init__(self, path="state.json", default_portions=47):
        self.path = path
        self.data = dict(self.DEFAULTS)
        self.data["portions"] = default_portions
        loaded = self._read(path)
        if loaded is None:
            loaded = self._read(path + ".tmp")   # nur wenn die Hauptdatei fehlt oder kaputt ist
        if loaded:
            for key in self.DEFAULTS:
                if key in loaded:
                    self.data[key] = loaded[key]

    @staticmethod
    def _read(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def __getitem__(self, key):
        return self.data[key]

    def update(self, **kw):
        self.data.update(kw)
        self.save()

    def save(self):
        """Schreibt in eine Hilfsdatei und ersetzt dann die alte in einem Schritt. Ein Abbruch dazwischen laesst
        die alte Datei stehen, so gehen Position und Token nicht verloren."""
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.data, f)
        try:
            os.rename(tmp, self.path)   # ersetzt eine vorhandene Datei, auch im Flash des Pico
        except OSError:
            os.remove(self.path)
            os.rename(tmp, self.path)

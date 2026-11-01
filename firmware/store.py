"""Zustand im Flash: Position, Scheibe und BLE-Token. Wird vor und nach jeder Fahrt geschrieben."""
import json
import os


class Store:
    DEFAULTS = {"k": 0, "portions": 47, "dirty": False, "token": ""}

    def __init__(self, path="state.json", default_portions=47):
        self.path = path
        self.data = dict(self.DEFAULTS)
        self.data["portions"] = default_portions
        try:
            with open(path) as f:
                loaded = json.load(f)
            for key in self.DEFAULTS:
                if key in loaded:
                    self.data[key] = loaded[key]
        except (OSError, ValueError):
            pass

    def __getitem__(self, key):
        return self.data[key]

    def update(self, **kw):
        self.data.update(kw)
        self.save()

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.data, f)
        try:
            os.remove(self.path)
        except OSError:
            pass
        os.rename(tmp, self.path)

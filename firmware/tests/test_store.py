import json
import os
import unittest

import fakes  # noqa: F401
from fakes import make_store
from store import Store


class StoreTest(unittest.TestCase):
    def test_roundtrip(self):
        store, path = make_store(k=5, token="abc")
        again = Store(path)
        self.assertEqual(again["k"], 5)
        self.assertEqual(again["token"], "abc")

    def test_save_replaces_and_leaves_no_tmp(self):
        store, path = make_store(k=1)
        store.update(k=2)
        self.assertFalse(os.path.exists(path + ".tmp"))
        self.assertEqual(json.load(open(path))["k"], 2)

    def test_interrupted_save_keeps_the_old_file(self):
        store, path = make_store(k=3, token="abc")
        with open(path + ".tmp", "w") as f:   # Abbruch waehrend des Schreibens
            f.write('{"k": 4, "tok')
        again = Store(path)
        self.assertEqual(again["k"], 3)
        self.assertEqual(again["token"], "abc")

    def test_tmp_is_used_only_without_the_main_file(self):
        store, path = make_store(k=3, token="abc")
        with open(path + ".tmp", "w") as f:
            json.dump({"k": 9, "token": "new", "portions": 47, "dirty": False}, f)
        self.assertEqual(Store(path)["k"], 3)
        os.remove(path)
        self.assertEqual(Store(path)["k"], 9)

    def test_missing_files_give_defaults(self):
        store, path = make_store()
        os.remove(path) if os.path.exists(path) else None
        again = Store(path)
        self.assertEqual(again["k"], 0)
        self.assertEqual(again["token"], "")


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest


class TestKeepAlive(unittest.TestCase):
    def test_keepalive_run_once_updates_report(self):
        import nexus_supabase_keepalive as ka

        with tempfile.TemporaryDirectory() as td:
            base_dir = td
            cfg_dir = os.path.join(base_dir, "CONFIG")
            os.makedirs(cfg_dir, exist_ok=True)

            calls = {"n": 0}

            def ping_fn(timeout_sec: int):
                calls["n"] += 1
                return True, f"ok_timeout_{timeout_sec}"

            keep = ka.SupabaseKeepAlive(base_dir, cfg_dir, ping_fn=ping_fn)
            rep = keep.run_once()
            self.assertTrue(rep.get("ok"))
            self.assertEqual(calls["n"], 1)
            self.assertTrue(os.path.exists(os.path.join(cfg_dir, "supabase_keepalive_last.json")))


if __name__ == "__main__":
    unittest.main()

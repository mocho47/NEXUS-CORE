import os
import time
import json
import tempfile
import unittest


class TestHousekeeping(unittest.TestCase):
    def test_housekeeping_dry_run_and_delete(self):
        import nexus_housekeeping

        with tempfile.TemporaryDirectory() as td:
            base_dir = td
            cfg_dir = os.path.join(base_dir, "CONFIG")
            os.makedirs(cfg_dir, exist_ok=True)

            logs_dir = os.path.join(base_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)

            # Crear archivos candidatos
            old_perf = os.path.join(logs_dir, "perf_snapshot_20000101_000000.json")
            with open(old_perf, "w", encoding="utf-8") as f:
                json.dump({"ok": True}, f)

            old_log = os.path.join(logs_dir, "old.log")
            with open(old_log, "w", encoding="utf-8") as f:
                f.write("x")

            voice_old = os.path.join(base_dir, "voice_old.mp3")
            with open(voice_old, "wb") as f:
                f.write(b"0" * 10)

            temp_dir = os.path.join(base_dir, "DESCARGA_TEMPORAL")
            os.makedirs(temp_dir, exist_ok=True)
            temp_old = os.path.join(temp_dir, "tmp.bin")
            with open(temp_old, "wb") as f:
                f.write(b"1" * 10)

            # Hacerlos viejos
            very_old_ts = time.time() - (60 * 60 * 24 * 40)
            for p in [old_perf, old_log, voice_old, temp_old]:
                os.utime(p, (very_old_ts, very_old_ts))

            hk = nexus_housekeeping.Housekeeping(base_dir, cfg_dir)
            # Forzar umbrales cortos
            hk._config.logs_keep_days = 1
            hk._config.perf_keep_days = 1
            hk._config.voice_keep_days = 1
            hk._config.temp_keep_days = 1
            hk._config.max_voice_files = 200
            hk._config.enabled = True
            hk._config.report_only = True
            hk.save_config()

            rep = hk.run(allow_delete=False)
            self.assertGreaterEqual(len(rep.get("planned") or []), 3)
            self.assertTrue(os.path.exists(old_perf))

            # Ahora borrar
            hk.set_report_only(False)
            rep2 = hk.run(allow_delete=True)
            self.assertGreaterEqual(len(rep2.get("planned") or []), 3)
            self.assertFalse(os.path.exists(old_perf))
            self.assertFalse(os.path.exists(old_log))
            self.assertFalse(os.path.exists(voice_old))
            self.assertFalse(os.path.exists(temp_old))


if __name__ == "__main__":
    unittest.main()

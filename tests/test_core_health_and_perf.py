import os
import sys
import subprocess
import unittest


def _run_py(code: str, timeout: int = 120) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault("NEXUS_NO_AUTOSTART", "1")
    env.setdefault("NEXUS_PRIVACY_MODE", "offline")
    env.setdefault("NEXUS_DISABLE_CLOUD", "1")
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )


class TestCoreHealthAndPerf(unittest.TestCase):
    def test_self_heal_healthcheck_structure(self):
        code = """
import json
import nexus_self_heal
hc = nexus_self_heal.healthcheck()
print(json.dumps({
  'has_required': isinstance(hc.get('required'), list),
  'has_optional': isinstance(hc.get('optional'), list),
  'has_dirs': isinstance(hc.get('dirs'), list)
}))
""".strip()
        proc = _run_py(code)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
        self.assertIn("has_required", proc.stdout)
        self.assertIn("has_optional", proc.stdout)
        self.assertIn("has_dirs", proc.stdout)

    def test_self_heal_module_names_and_mapping(self):
        code = """
import nexus_self_heal
hc = nexus_self_heal.healthcheck()
mods = [x.get('module') for x in (hc.get('required') or [])]
print('has_speech_recognition=' + str('speech_recognition' in mods))
print('has_old_speechrecognition=' + str('SpeechRecognition' in mods))
print('map=' + str(nexus_self_heal.module_to_pip('speech_recognition')))
""".strip()
        proc = _run_py(code)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
        self.assertIn("has_speech_recognition=True", proc.stdout)
        self.assertIn("has_old_speechrecognition=False", proc.stdout)
        self.assertIn("map=SpeechRecognition", proc.stdout)

    def test_capture_perf_snapshot_writes_file(self):
        code = """
import os
import json
import nexus_core
payload, out_path = nexus_core.capture_perf_snapshot(reason='test')
print('path=' + str(out_path))
print('payload_ok=' + str(isinstance(payload, dict)))
print('exists=' + str(bool(out_path) and os.path.exists(out_path)))
""".strip()
        proc = _run_py(code)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
        self.assertIn("payload_ok=True", proc.stdout)
        self.assertIn("exists=True", proc.stdout)

    def test_actions_auto_window_toggle(self):
        code = """
import time
import nexus_core
nexus_core.clear_actions_auto_window()
print('enabled0=' + str(nexus_core.actions_auto_enabled()))
nexus_core.set_actions_auto_window(1)
print('enabled1=' + str(nexus_core.actions_auto_enabled()))
# revoca
nexus_core.clear_actions_auto_window()
print('enabled2=' + str(nexus_core.actions_auto_enabled()))
""".strip()
        proc = _run_py(code)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
        self.assertIn("enabled0=False", proc.stdout)
        self.assertIn("enabled1=True", proc.stdout)
        self.assertIn("enabled2=False", proc.stdout)


if __name__ == "__main__":
    unittest.main()

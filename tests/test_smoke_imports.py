import os
import sys
import subprocess
import unittest


def _run_py(code: str, env: dict | None = None, timeout: int = 90) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    # Modo seguro para pruebas: evita auto-arranque de hilos globales en imports.
    merged_env.setdefault("NEXUS_NO_AUTOSTART", "1")
    merged_env.setdefault("NEXUS_PRIVACY_MODE", "offline")
    merged_env.setdefault("NEXUS_DISABLE_CLOUD", "1")
    if env:
        merged_env.update({k: str(v) for k, v in env.items()})
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=merged_env,
        timeout=timeout,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )


class TestSmokeImports(unittest.TestCase):
    def test_import_core(self):
        proc = _run_py("import nexus_core; print('ok')")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
        self.assertIn("ok", proc.stdout)

    def test_import_key_modules(self):
        modules = [
            "nexus_memory",
            "nexus_ecosystem",
            "nexus_watchtower",
            "nexus_social_operator",
            "nexus_self_heal",
            "nexus_vault",
            "nexus_video_maker",
        ]
        code = "\n".join([f"import {m}" for m in modules] + ["print('ok')"])
        proc = _run_py(code)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
        self.assertIn("ok", proc.stdout)

    def test_import_core_offline_dns_failure_simulated(self):
        # Simula que todo DNS falla: el core debe seguir importando (usa fallbacks)
        code = """
import socket
_real_getaddrinfo = socket.getaddrinfo

def _fail(*args, **kwargs):
    raise OSError(11001, 'getaddrinfo failed')

socket.getaddrinfo = _fail
try:
    import nexus_core
    print('ok')
finally:
    socket.getaddrinfo = _real_getaddrinfo
""".strip()
        proc = _run_py(code)
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
        self.assertIn("ok", proc.stdout)


if __name__ == "__main__":
    unittest.main()

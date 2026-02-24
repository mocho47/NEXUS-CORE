import os
import unittest


class TestDoctor(unittest.TestCase):
    def test_doctor_runs_offline_safe(self):
        # Ensure safe import mode
        os.environ["NEXUS_NO_AUTOSTART"] = "1"
        os.environ["NEXUS_PRIVACY_MODE"] = "offline"
        os.environ["NEXUS_DISABLE_CLOUD"] = "1"

        import nexus_doctor

        rep = nexus_doctor.run_doctor(
            base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            config_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "CONFIG")),
            cloud_allowed=False,
            timeout_sec=2,
            ping_keepalive_fn=None,
            local_healthcheck_fn=None,
        )

        self.assertIsInstance(rep, dict)
        self.assertIn("findings", rep)
        self.assertIn("ok", rep)
        # In offline/disabled cloud, it should not crash and should report cloud not allowed
        findings = rep.get("findings") or []
        self.assertTrue(any(f.get("name") == "cloud:allowed" for f in findings if isinstance(f, dict)))


if __name__ == "__main__":
    unittest.main()

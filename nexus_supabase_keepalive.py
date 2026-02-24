import os
import json
import time
import random
import threading
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Optional, Tuple


DEFAULT_CONFIG_NAME = "supabase_keepalive.json"


def _now() -> float:
    return time.time()


def _safe_bool(x, default: bool) -> bool:
    try:
        if isinstance(x, bool):
            return x
        if isinstance(x, str):
            return x.strip().lower() in ("1", "true", "yes", "on")
        return bool(x)
    except Exception:
        return default


def _safe_int(x, default: int) -> int:
    try:
        return int(x)
    except Exception:
        return default


@dataclass
class KeepAliveConfig:
    enabled: bool = True
    interval_sec: int = 12 * 60 * 60
    jitter_sec: int = 10 * 60
    timeout_sec: int = 8

    last_ok_ts: float = 0.0
    last_error_ts: float = 0.0
    last_error: str = ""


class SupabaseKeepAlive:
    """Mantiene actividad mínima del proyecto Supabase.

    - NO hace scraping ni acciones destructivas.
    - Solo ejecuta un "ping" configurable (función inyectada).
    - Debe estar gateado por privacidad: allow_cb controla si se permite red.
    """

    def __init__(
        self,
        base_dir: str,
        config_dir: str,
        ping_fn: Callable[[int], Tuple[bool, str]],
    ):
        self.base_dir = os.path.abspath(base_dir)
        self.config_dir = os.path.abspath(config_dir)
        self._config_path = os.path.join(self.config_dir, DEFAULT_CONFIG_NAME)
        self._last_report_path = os.path.join(self.config_dir, "supabase_keepalive_last.json")
        self._ping_fn = ping_fn

        self._config = self.load_config()
        self._stop = False
        self._thread: Optional[threading.Thread] = None

    def load_config(self) -> KeepAliveConfig:
        os.makedirs(self.config_dir, exist_ok=True)
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                base = asdict(KeepAliveConfig())
                merged = {**base, **{k: v for k, v in data.items() if k in base}}
                cfg = KeepAliveConfig(**merged)
                # sanity
                cfg.interval_sec = max(15 * 60, _safe_int(cfg.interval_sec, 12 * 3600))
                cfg.jitter_sec = max(0, _safe_int(cfg.jitter_sec, 600))
                cfg.timeout_sec = max(2, _safe_int(cfg.timeout_sec, 8))
                cfg.enabled = _safe_bool(cfg.enabled, True)
                return cfg
            except Exception:
                return KeepAliveConfig()

        cfg = KeepAliveConfig()
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return cfg

    def save_config(self) -> None:
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self._config), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_config(self) -> KeepAliveConfig:
        return self._config

    def set_enabled(self, enabled: bool) -> None:
        self._config.enabled = bool(enabled)
        self.save_config()

    def run_once(self) -> Dict:
        cfg = self._config
        ok, msg = False, "no_ping"
        try:
            ok, msg = self._ping_fn(int(cfg.timeout_sec))
        except Exception as e:
            ok, msg = False, str(e)

        now_ts = _now()
        if ok:
            cfg.last_ok_ts = now_ts
            cfg.last_error = ""
        else:
            cfg.last_error_ts = now_ts
            cfg.last_error = str(msg or "error")[:500]
        self.save_config()

        report = {
            "ts": now_ts,
            "ok": bool(ok),
            "message": str(msg),
            "enabled": bool(cfg.enabled),
            "interval_sec": int(cfg.interval_sec),
            "jitter_sec": int(cfg.jitter_sec),
            "timeout_sec": int(cfg.timeout_sec),
            "last_ok_ts": float(cfg.last_ok_ts or 0.0),
            "last_error_ts": float(cfg.last_error_ts or 0.0),
            "last_error": str(cfg.last_error or ""),
        }

        try:
            with open(self._last_report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return report

    def start(self, allow_cb: Callable[[], bool]) -> None:
        if self._thread and self._thread.is_alive():
            return

        def loop():
            while not self._stop:
                try:
                    cfg = self._config
                    if cfg.enabled and bool(allow_cb()):
                        self.run_once()

                    sleep_base = int(cfg.interval_sec)
                    jitter = int(cfg.jitter_sec)
                    if jitter > 0:
                        sleep_base += random.randint(0, jitter)
                    # sleep in chunks so stop is responsive
                    remaining = max(30, sleep_base)
                    while remaining > 0 and not self._stop:
                        step = min(30, remaining)
                        time.sleep(step)
                        remaining -= step
                except Exception:
                    time.sleep(60)

        self._stop = False
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop = True

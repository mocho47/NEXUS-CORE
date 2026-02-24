import os
import time
import json
import glob
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


DEFAULT_CONFIG_NAME = "housekeeping.json"


def _now() -> float:
    return time.time()


def _safe_int(x, default: int) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _safe_float(x, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _is_file(p: str) -> bool:
    try:
        return os.path.isfile(p)
    except Exception:
        return False


def _file_age_seconds(p: str, now_ts: Optional[float] = None) -> Optional[float]:
    try:
        ts = os.path.getmtime(p)
        return (now_ts or _now()) - ts
    except Exception:
        return None


@dataclass
class HousekeepingConfig:
    enabled: bool = True
    interval_sec: int = 30 * 60

    # Por seguridad, limpiamos solo carpetas/patrones controlados.
    logs_keep_days: int = 30
    perf_keep_days: int = 30
    voice_keep_days: int = 14
    temp_keep_days: int = 7

    # Límites extra
    max_voice_files: int = 200

    # Modo seguro: si True, solo reporta. Si False, borra dentro de targets.
    report_only: bool = False


class Housekeeping:
    def __init__(self, base_dir: str, config_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir)
        self.config_dir = os.path.abspath(config_dir or os.path.join(self.base_dir, "CONFIG"))
        self._config_path = os.path.join(self.config_dir, DEFAULT_CONFIG_NAME)
        self._config = self.load_config()
        self._last_report_path = os.path.join(self.config_dir, "housekeeping_last.json")
        self._stop = False
        self._thread: Optional[threading.Thread] = None

    def load_config(self) -> HousekeepingConfig:
        os.makedirs(self.config_dir, exist_ok=True)
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cfg = HousekeepingConfig(**{**asdict(HousekeepingConfig()), **(data or {})})
                return cfg
            except Exception:
                return HousekeepingConfig()
        cfg = HousekeepingConfig()
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

    def set_enabled(self, enabled: bool) -> None:
        self._config.enabled = bool(enabled)
        self.save_config()

    def set_report_only(self, report_only: bool) -> None:
        self._config.report_only = bool(report_only)
        self.save_config()

    def get_config(self) -> HousekeepingConfig:
        return self._config

    def _targets(self) -> Dict[str, Dict]:
        # IMPORTANT: solo targets de basura generada por NEXUS
        return {
            "logs_dir": {
                "type": "dir_age",
                "path": os.path.join(self.base_dir, "logs"),
                "keep_days": self._config.logs_keep_days,
                "extensions": [".log", ".txt", ".json"],
            },
            "perf_snapshots": {
                "type": "glob_age",
                "pattern": os.path.join(self.base_dir, "logs", "perf_snapshot_*.json"),
                "keep_days": self._config.perf_keep_days,
            },
            "temp_downloads": {
                "type": "dir_age",
                "path": os.path.join(self.base_dir, "DESCARGA_TEMPORAL"),
                "keep_days": self._config.temp_keep_days,
                "extensions": None,
            },
            "voice_mp3_root": {
                "type": "glob_age_and_count",
                "pattern": os.path.join(self.base_dir, "voice_*.mp3"),
                "keep_days": self._config.voice_keep_days,
                "max_files": self._config.max_voice_files,
            },
        }

    def _collect_candidates(self, now_ts: float) -> List[Tuple[str, str]]:
        # Retorna lista de (path, reason)
        candidates: List[Tuple[str, str]] = []
        targets = self._targets()

        for name, t in targets.items():
            ttype = t.get("type")
            if ttype == "dir_age":
                d = t.get("path")
                keep_days = _safe_int(t.get("keep_days"), 30)
                exts = t.get("extensions")
                if not d or not os.path.isdir(d):
                    continue
                try:
                    for root, _dirs, files in os.walk(d):
                        for fn in files:
                            p = os.path.join(root, fn)
                            if exts and os.path.splitext(fn)[1].lower() not in set([e.lower() for e in exts]):
                                continue
                            age = _file_age_seconds(p, now_ts)
                            if age is None:
                                continue
                            if age >= keep_days * 86400:
                                candidates.append((p, f"{name}:older_than_{keep_days}d"))
                except Exception:
                    continue

            elif ttype == "glob_age":
                pattern = t.get("pattern")
                keep_days = _safe_int(t.get("keep_days"), 30)
                if not pattern:
                    continue
                for p in glob.glob(pattern):
                    if not _is_file(p):
                        continue
                    age = _file_age_seconds(p, now_ts)
                    if age is None:
                        continue
                    if age >= keep_days * 86400:
                        candidates.append((p, f"{name}:older_than_{keep_days}d"))

            elif ttype == "glob_age_and_count":
                pattern = t.get("pattern")
                keep_days = _safe_int(t.get("keep_days"), 14)
                max_files = _safe_int(t.get("max_files"), 200)
                if not pattern:
                    continue
                files = [p for p in glob.glob(pattern) if _is_file(p)]

                # Por edad
                for p in files:
                    age = _file_age_seconds(p, now_ts)
                    if age is None:
                        continue
                    if age >= keep_days * 86400:
                        candidates.append((p, f"{name}:older_than_{keep_days}d"))

                # Por conteo: si excede max_files, borrar los más viejos
                if len(files) > max_files:
                    try:
                        files.sort(key=lambda fp: os.path.getmtime(fp))
                        overflow = files[: max(0, len(files) - max_files)]
                        for p in overflow:
                            candidates.append((p, f"{name}:overflow_gt_{max_files}"))
                    except Exception:
                        pass

        # Dedup
        seen = set()
        uniq: List[Tuple[str, str]] = []
        for p, r in candidates:
            if p not in seen:
                seen.add(p)
                uniq.append((p, r))
        return uniq

    def run(self, allow_delete: bool = False) -> Dict:
        now_ts = _now()
        cfg = self._config
        candidates = self._collect_candidates(now_ts)

        deleted: List[Dict] = []
        errors: List[Dict] = []

        do_delete = bool(allow_delete) and (not cfg.report_only)

        if do_delete:
            for p, reason in candidates:
                # Freno extra: nunca borrar fuera de base_dir
                try:
                    ap = os.path.abspath(p)
                    if not ap.startswith(self.base_dir + os.sep):
                        continue
                except Exception:
                    continue

                try:
                    os.remove(p)
                    deleted.append({"path": p, "reason": reason})
                except Exception as e:
                    errors.append({"path": p, "reason": reason, "error": str(e)})

        report = {
            "ts": now_ts,
            "enabled": cfg.enabled,
            "report_only": cfg.report_only,
            "allow_delete": bool(allow_delete),
            "planned": [{"path": p, "reason": r} for p, r in candidates],
            "deleted": deleted,
            "errors": errors,
        }

        # Auditoría local (no crece infinito, se sobreescribe)
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self._last_report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return report

    def start(self, allow_delete_cb=None) -> None:
        if self._thread and self._thread.is_alive():
            return

        def loop():
            while not self._stop:
                try:
                    cfg = self._config
                    if cfg.enabled:
                        allow_delete = False
                        try:
                            if callable(allow_delete_cb):
                                allow_delete = bool(allow_delete_cb())
                        except Exception:
                            allow_delete = False
                        self.run(allow_delete=allow_delete)
                    time.sleep(max(30, int(cfg.interval_sec)))
                except Exception:
                    time.sleep(60)

        self._stop = False
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop = True

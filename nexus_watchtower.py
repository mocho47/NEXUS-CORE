import json
import os
import threading
import time
from typing import Callable, Dict, List, Optional


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DROP_IN_DIR = os.path.join(BASE_DIR, "DROP_IN")
INBOX_DIR = os.path.join(DROP_IN_DIR, "INBOX")
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")
STATE_FILE = os.path.join(CONFIG_DIR, "watchtower_state.json")


def _safe_load_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _safe_write_json(path: str, data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _now() -> float:
    return time.time()


class Watchtower:
    """Monitor local: ingiere mensajes/eventos desde DROP_IN/INBOX.

    Formatos soportados:
    - *.json (dict): {source, from, text, ts, url, type}
    - *.txt: el contenido se vuelve text, source='inbox'

    No se conecta a la web. Es un puente seguro: tú/tu sistema deciden qué llega al INBOX.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._unread: List[Dict] = []
        self._seen_files = set()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._load_state()

    def _load_state(self) -> None:
        state = _safe_load_json(STATE_FILE) or {}
        seen = state.get("seen_files")
        if isinstance(seen, list):
            self._seen_files = set(str(x) for x in seen)

    def _save_state(self) -> None:
        state = {"seen_files": sorted(list(self._seen_files))[-5000:]}
        _safe_write_json(STATE_FILE, state)

    def start(self, on_event: Optional[Callable[[Dict], None]] = None, poll_sec: float = 1.0) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run():
            os.makedirs(INBOX_DIR, exist_ok=True)
            while not self._stop.is_set():
                try:
                    self._scan_once(on_event=on_event)
                except Exception:
                    pass
                self._stop.wait(max(0.25, float(poll_sec)))

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _scan_once(self, on_event: Optional[Callable[[Dict], None]] = None) -> None:
        try:
            names = os.listdir(INBOX_DIR)
        except Exception:
            return

        # Procesar en orden de mtime para que se lea "natural"
        paths = []
        for name in names:
            if name.startswith("."):
                continue
            p = os.path.join(INBOX_DIR, name)
            if not os.path.isfile(p):
                continue
            paths.append(p)

        try:
            paths.sort(key=lambda p: os.path.getmtime(p))
        except Exception:
            pass

        for path in paths:
            if path in self._seen_files:
                continue

            evt = self._parse_file(path)
            if evt is None:
                # igual marcamos visto para no ciclar
                self._seen_files.add(path)
                continue

            evt.setdefault("received_ts", _now())
            evt.setdefault("path", path)

            with self._lock:
                self._unread.append(evt)

            self._seen_files.add(path)
            self._save_state()

            if on_event:
                try:
                    on_event(evt)
                except Exception:
                    pass

    def _parse_file(self, path: str) -> Optional[Dict]:
        name = os.path.basename(path)
        lower = name.lower()

        if lower.endswith(".json"):
            data = _safe_load_json(path)
            if not data:
                return None
            # normalizar claves mínimas
            if "text" not in data:
                return None
            data.setdefault("source", "inbox")
            data.setdefault("from", data.get("sender") or "")
            data.setdefault("type", "message")
            return data

        if lower.endswith(".txt"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
            except Exception:
                return None
            if not text:
                return None
            return {"source": "inbox", "from": "", "text": text, "type": "note"}

        return None

    def unread_count(self) -> int:
        with self._lock:
            return len(self._unread)

    def pop_unread(self, limit: int = 5) -> List[Dict]:
        with self._lock:
            items = self._unread[: max(0, int(limit))]
            self._unread = self._unread[len(items) :]
        return items

    def peek_unread(self, limit: int = 5) -> List[Dict]:
        with self._lock:
            return list(self._unread[: max(0, int(limit))])

    def clear_unread(self) -> None:
        with self._lock:
            self._unread = []

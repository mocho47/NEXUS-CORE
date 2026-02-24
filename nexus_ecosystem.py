import json
import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


def _now_ts() -> float:
    return time.time()


def _norm(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip().lower()
    text = re.sub(r"[\s\-_]+", " ", text)
    text = re.sub(r"[^a-z0-9áéíóúñü ./:\\]", "", text)
    return text.strip()


def _basename_no_ext(path: str) -> str:
    base = os.path.basename(path)
    if "." in base:
        return base.rsplit(".", 1)[0]
    return base


@dataclass
class EcosystemHit:
    kind: str  # file|folder|alias
    name: str
    path: str
    score: int


class EcosystemIndex:
    def __init__(
        self,
        base_dir: str,
        config_dir: str,
        index_filename: str = "ecosystem_index.json",
        aliases_filename: str = "ecosystem_aliases.json",
    ):
        self.base_dir = os.path.abspath(base_dir)
        self.config_dir = os.path.abspath(config_dir)
        self.index_path = os.path.join(self.config_dir, index_filename)
        self.aliases_path = os.path.join(self.config_dir, aliases_filename)

        self._lock = threading.Lock()
        self._index: Dict[str, object] = {
            "built_at": 0.0,
            "root": self.base_dir,
            "files": {},      # name_key -> [relpath]
            "folders": {},    # name_key -> [relpath]
        }
        self._aliases: Dict[str, str] = {}
        self._refresh_thread: Optional[threading.Thread] = None

        self._load_aliases()
        self._load_index()

    # -------------------- Persistencia --------------------
    def _load_index(self) -> None:
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and data.get("root") == self.base_dir:
                    with self._lock:
                        self._index = data
        except Exception:
            # Silencioso: no rompemos el core por esto
            pass

    def _save_index(self) -> None:
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_aliases(self) -> None:
        try:
            if os.path.exists(self.aliases_path):
                with open(self.aliases_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._aliases = {str(k): str(v) for k, v in data.items()}
        except Exception:
            pass

    def _save_aliases(self) -> None:
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.aliases_path, "w", encoding="utf-8") as f:
                json.dump(self._aliases, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # -------------------- Build / Refresh --------------------
    def start_background_refresh(self, max_age_hours: float = 24.0) -> None:
        with self._lock:
            built_at = float(self._index.get("built_at") or 0.0)
        too_old = (_now_ts() - built_at) > (max_age_hours * 3600.0)
        if too_old or built_at <= 0.0:
            self.refresh_async(force=True)

    def refresh_async(self, force: bool = False) -> None:
        if self._refresh_thread and self._refresh_thread.is_alive():
            return

        def _run():
            try:
                self.build_index(force=force)
            except Exception:
                pass

        self._refresh_thread = threading.Thread(target=_run, daemon=True)
        self._refresh_thread.start()

    def build_index(
        self,
        force: bool = False,
        max_files: int = 25000,
        max_file_size_mb: int = 25,
    ) -> None:
        # Evitar rebuild muy frecuente
        with self._lock:
            built_at = float(self._index.get("built_at") or 0.0)
        if (not force) and built_at and (_now_ts() - built_at) < 300:
            return

        excluded_dir_names = {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
            "OUTPUT",
            "OUTPUT_READY",
            "processed",
        }
        excluded_exts = {
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".wav",
            ".mp3",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".zip",
            ".7z",
            ".rar",
            ".exe",
            ".dll",
        }

        files_map: Dict[str, List[str]] = {}
        folders_map: Dict[str, List[str]] = {}

        max_bytes = max_file_size_mb * 1024 * 1024
        count = 0

        # Iterativo para evitar recursion deep
        stack = [self.base_dir]
        while stack and count < max_files:
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        try:
                            name = entry.name
                            if entry.is_dir(follow_symlinks=False):
                                if name in excluded_dir_names:
                                    continue
                                full = entry.path
                                rel = os.path.relpath(full, self.base_dir)
                                key = _norm(name)
                                folders_map.setdefault(key, []).append(rel)
                                stack.append(full)
                            elif entry.is_file(follow_symlinks=False):
                                ext = os.path.splitext(name)[1].lower()
                                if ext in excluded_exts:
                                    continue
                                try:
                                    if entry.stat().st_size > max_bytes:
                                        continue
                                except Exception:
                                    pass

                                full = entry.path
                                rel = os.path.relpath(full, self.base_dir)

                                key1 = _norm(name)
                                key2 = _norm(_basename_no_ext(name))
                                files_map.setdefault(key1, []).append(rel)
                                if key2 and key2 != key1:
                                    files_map.setdefault(key2, []).append(rel)
                                count += 1
                                if count >= max_files:
                                    break
                        except Exception:
                            continue
            except Exception:
                continue

        with self._lock:
            self._index = {
                "built_at": _now_ts(),
                "root": self.base_dir,
                "files": files_map,
                "folders": folders_map,
            }
        self._save_index()

    # -------------------- Alias / Learning --------------------
    def set_alias(self, alias: str, path: str) -> bool:
        alias_key = _norm(alias)
        if not alias_key:
            return False

        if not path:
            return False

        # Normalizar path
        path = path.strip().strip('"')
        if not os.path.isabs(path):
            # Interpretar como relativo a base_dir
            path = os.path.join(self.base_dir, path)
        path = os.path.abspath(path)

        if not os.path.exists(path):
            return False

        self._aliases[alias_key] = path
        self._save_aliases()
        return True

    def resolve_alias(self, text: str) -> Optional[str]:
        key = _norm(text)
        if not key:
            return None
        return self._aliases.get(key)

    # -------------------- Search --------------------
    def _score_key(self, key: str, query: str) -> int:
        if not key or not query:
            return 0
        if key == query:
            return 100
        if key.startswith(query):
            return 85
        if query in key:
            return 70
        # Token overlap
        k_tokens = set(key.split())
        q_tokens = set(query.split())
        overlap = len(k_tokens & q_tokens)
        return 40 + overlap * 6 if overlap else 0

    def search(self, query: str, kind: str = "any", max_results: int = 5) -> List[EcosystemHit]:
        q = _norm(query)
        if not q:
            return []

        hits: List[EcosystemHit] = []

        # Alias exacto primero
        alias_path = self._aliases.get(q)
        if alias_path:
            hits.append(EcosystemHit(kind="alias", name=q, path=alias_path, score=110))

        with self._lock:
            files_map = dict(self._index.get("files") or {})
            folders_map = dict(self._index.get("folders") or {})

        if kind in ("any", "folder"):
            for key, rels in folders_map.items():
                score = self._score_key(str(key), q)
                if score <= 0:
                    continue
                for rel in rels[:3]:
                    hits.append(
                        EcosystemHit(kind="folder", name=str(key), path=os.path.join(self.base_dir, rel), score=score)
                    )

        if kind in ("any", "file"):
            for key, rels in files_map.items():
                score = self._score_key(str(key), q)
                if score <= 0:
                    continue
                for rel in rels[:3]:
                    hits.append(
                        EcosystemHit(kind="file", name=str(key), path=os.path.join(self.base_dir, rel), score=score)
                    )

        hits.sort(key=lambda h: (h.score, -len(h.path)), reverse=True)
        # Deduplicar por path
        seen = set()
        out: List[EcosystemHit] = []
        for h in hits:
            if h.path in seen:
                continue
            seen.add(h.path)
            out.append(h)
            if len(out) >= max_results:
                break
        return out

    # -------------------- Info --------------------
    def status(self) -> Tuple[float, int, int, int]:
        with self._lock:
            built_at = float(self._index.get("built_at") or 0.0)
            files_map = self._index.get("files") or {}
            folders_map = self._index.get("folders") or {}
        return built_at, len(files_map), len(folders_map), len(self._aliases)

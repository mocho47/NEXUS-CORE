import os
import socket
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


def _now() -> float:
    return time.time()


def _safe_bool(x: Any, default: bool = False) -> bool:
    try:
        if isinstance(x, bool):
            return x
        if isinstance(x, str):
            return x.strip().lower() in ("1", "true", "yes", "on")
        return bool(x)
    except Exception:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    return _safe_bool(os.environ.get(name), default=default)


def _dns_resolves(hostname: str) -> Tuple[bool, str]:
    try:
        # getaddrinfo will raise socket.gaierror on NXDOMAIN/resolution failures
        socket.getaddrinfo(hostname, 443)
        return True, "ok"
    except Exception as e:
        return False, str(e)


def _tcp_connect(hostname: str, port: int, timeout_sec: int = 4) -> Tuple[bool, str]:
    try:
        with socket.create_connection((hostname, port), timeout=max(1, int(timeout_sec))):
            return True, "ok"
    except Exception as e:
        return False, str(e)


def _read_env_supabase_url() -> str:
    url = (
        os.environ.get("SUPABASE_URL")
        or os.environ.get("SUPABASE_PROJECT_URL")
        or os.environ.get("SUPABASE_REST_URL")
        or ""
    ).strip()
    return url


def _extract_hostname(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    # very small parser to avoid extra deps
    u = u.replace("https://", "").replace("http://", "")
    u = u.split("/", 1)[0]
    return u.strip()


@dataclass
class DoctorFinding:
    name: str
    ok: bool
    details: str = ""
    severity: str = "info"  # info|warn|error


def run_doctor(
    base_dir: str,
    config_dir: str,
    *,
    cloud_allowed: bool,
    timeout_sec: int = 6,
    ping_keepalive_fn=None,
    local_healthcheck_fn=None,
) -> Dict[str, Any]:
    """End-to-end diagnostic report (no destructive actions).

    Goals:
    - Confirm local health (deps/assets) if available.
    - Confirm cloud config is sane (SUPABASE_URL present, resolves, TCP reachable).
    - Optionally run keepalive ping (HTTP) when cloud is allowed.

    This function must be safe to call in tests: no autostart, no infinite loops.
    """

    base_dir = os.path.abspath(base_dir)
    config_dir = os.path.abspath(config_dir)

    findings: List[DoctorFinding] = []

    # --- Local: directories that must exist ---
    for rel in ["CONFIG", "DROP_IN", os.path.join("DROP_IN", "INBOX")]:
        path = os.path.join(base_dir, rel)
        try:
            os.makedirs(path, exist_ok=True)
            findings.append(DoctorFinding(name=f"dir:{rel}", ok=True, details=path))
        except Exception as e:
            findings.append(DoctorFinding(name=f"dir:{rel}", ok=False, details=str(e), severity="error"))

    # --- Local: optional healthcheck (existing self-heal healthcheck) ---
    hc_summary = None
    hc = None
    if callable(local_healthcheck_fn):
        try:
            hc = local_healthcheck_fn() or {}
            # Minimal summary
            missing_req = [x.get("module") for x in (hc.get("required") or []) if isinstance(x, dict) and not x.get("ok")]
            missing_files = [x.get("name") for x in (hc.get("files") or []) if isinstance(x, dict) and not x.get("ok")]
            hc_summary = {
                "missing_required": [m for m in missing_req if m],
                "missing_files": [m for m in missing_files if m],
            }
            findings.append(
                DoctorFinding(
                    name="local:healthcheck",
                    ok=(len(hc_summary["missing_required"]) == 0 and len(hc_summary["missing_files"]) == 0),
                    details=f"missing_required={len(hc_summary['missing_required'])}, missing_files={len(hc_summary['missing_files'])}",
                    severity="warn" if (hc_summary["missing_required"] or hc_summary["missing_files"]) else "info",
                )
            )
        except Exception as e:
            findings.append(DoctorFinding(name="local:healthcheck", ok=False, details=str(e), severity="warn"))

    # --- Cloud gating ---
    privacy_mode = (os.environ.get("NEXUS_PRIVACY_MODE", "supervised") or "supervised").strip().lower()
    disable_cloud = _env_bool("NEXUS_DISABLE_CLOUD", default=False)
    findings.append(
        DoctorFinding(
            name="cloud:allowed",
            ok=bool(cloud_allowed) and (privacy_mode != "offline") and (not disable_cloud),
            details=f"cloud_allowed={bool(cloud_allowed)}, privacy_mode={privacy_mode}, NEXUS_DISABLE_CLOUD={int(disable_cloud)}",
            severity="warn" if not cloud_allowed else "info",
        )
    )

    # --- Supabase URL and DNS/TCP ---
    supabase_url = _read_env_supabase_url()
    hostname = _extract_hostname(supabase_url)

    if not supabase_url:
        findings.append(DoctorFinding(name="cloud:supabase_url", ok=False, details="missing SUPABASE_URL", severity="error"))
    else:
        findings.append(DoctorFinding(name="cloud:supabase_url", ok=True, details=supabase_url))

    if hostname:
        ok_dns, dns_msg = _dns_resolves(hostname)
        findings.append(
            DoctorFinding(
                name="cloud:dns",
                ok=ok_dns,
                details=f"{hostname} -> {dns_msg}",
                severity="error" if not ok_dns else "info",
            )
        )

        ok_tcp, tcp_msg = _tcp_connect(hostname, 443, timeout_sec=timeout_sec)
        findings.append(
            DoctorFinding(
                name="cloud:tcp_443",
                ok=ok_tcp,
                details=f"{hostname}:443 -> {tcp_msg}",
                severity="warn" if not ok_tcp else "info",
            )
        )
    else:
        if supabase_url:
            findings.append(DoctorFinding(name="cloud:hostname", ok=False, details="could_not_parse_hostname", severity="error"))

    # --- Keepalive ping (HTTP) ---
    keepalive_report: Optional[Dict[str, Any]] = None
    if callable(ping_keepalive_fn) and cloud_allowed and supabase_url and hostname:
        try:
            ok_ping, ping_msg = ping_keepalive_fn(int(timeout_sec))
            keepalive_report = {"ok": bool(ok_ping), "message": str(ping_msg)[:800]}
            findings.append(
                DoctorFinding(
                    name="cloud:keepalive_ping",
                    ok=bool(ok_ping),
                    details=str(ping_msg)[:300],
                    severity="warn" if not ok_ping else "info",
                )
            )
        except Exception as e:
            keepalive_report = {"ok": False, "message": str(e)[:800]}
            findings.append(DoctorFinding(name="cloud:keepalive_ping", ok=False, details=str(e), severity="warn"))

    ok_all = all(f.ok for f in findings if f.severity in ("error", "warn"))

    report = {
        "ts": _now(),
        "ok": bool(ok_all),
        "base_dir": base_dir,
        "config_dir": config_dir,
        "supabase_url": supabase_url,
        "supabase_host": hostname,
        "findings": [asdict(f) for f in findings],
        "local_healthcheck": hc_summary,
        "keepalive": keepalive_report,
    }

    return report


def summarize_report(report: Dict[str, Any]) -> Tuple[str, List[str]]:
    findings = report.get("findings") or []
    errors = [f for f in findings if isinstance(f, dict) and (not f.get("ok")) and f.get("severity") == "error"]
    warns = [f for f in findings if isinstance(f, dict) and (not f.get("ok")) and f.get("severity") == "warn"]

    summary = f"Doctor: errores {len(errors)}, advertencias {len(warns)}."

    next_steps: List[str] = []
    # Prioritize common blockers
    for f in errors:
        name = f.get("name")
        if name == "cloud:supabase_url":
            next_steps.append("Configura SUPABASE_URL desde Supabase Dashboard > Settings > API > Project URL")
        if name == "cloud:dns":
            next_steps.append("DNS no resuelve el host de Supabase; revisa que SUPABASE_URL sea correcto")
        if name == "local:healthcheck":
            next_steps.append("Faltan dependencias/recursos locales; corre 'autorreparar' (supervisado)")

    if not next_steps and (errors or warns):
        next_steps.append("Revisa el reporte en consola para el detalle")

    return summary, next_steps

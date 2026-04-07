"""
motors/motor_auth.py — NEXUS v3 by Simplex
Motor de autenticación — puerto 8006
Generado por Z.ai
"""
import os
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Importar lib de auth
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.auth import (
    verify_pin, set_pin, create_session, get_session,
    has_permission, invalidate_session, get_active_sessions_count, ROLES_DB
)

app = FastAPI(title="NEXUS Auth Motor", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    rol: str
    pin: str


class SetPinRequest(BaseModel):
    rol: str
    pin: str
    admin_token: str


class VerifyRequest(BaseModel):
    token: str
    permiso: str = None


@app.post("/auth/login")
async def login(req: LoginRequest, request: Request):
    """Autenticar con rol + PIN. Retorna token de sesión."""
    ip = request.client.host if request.client else "unknown"

    if verify_pin(req.rol, req.pin, ip):
        token = create_session(req.rol)
        return {
            "ok": True,
            "token": token,
            "rol": req.rol,
            "nombre": ROLES_DB.get(req.rol, {}).get("nombre", req.rol)
        }
    else:
        raise HTTPException(status_code=401, detail="PIN incorrecto o cuenta bloqueada")


@app.post("/auth/verify")
async def verify(req: VerifyRequest):
    """Verificar token y opcionalmente chequear permiso."""
    session = get_session(req.token)
    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

    resultado = {
        "ok": True,
        "rol": session["rol"],
        "user_id": session["user_id"]
    }

    if req.permiso:
        resultado["tiene_permiso"] = has_permission(req.token, req.permiso)

    return resultado


@app.post("/auth/logout")
async def logout(req: VerifyRequest):
    """Cerrar sesión."""
    invalidate_session(req.token)
    return {"ok": True, "mensaje": "Sesión cerrada"}


@app.post("/auth/set-pin")
async def configurar_pin(req: SetPinRequest):
    """Configurar PIN de un rol (requiere token admin)."""
    session = get_session(req.admin_token)
    if not session or not has_permission(req.admin_token, "*"):
        raise HTTPException(status_code=403, detail="Se requiere acceso admin")

    if set_pin(req.rol, req.pin):
        return {"ok": True, "mensaje": f"PIN configurado para rol '{req.rol}'"}
    else:
        raise HTTPException(status_code=400, detail=f"Rol '{req.rol}' no existe")


@app.get("/auth/estado")
async def estado():
    """Estado del sistema de auth."""
    roles_configurados = [r for r, d in ROLES_DB.items() if d.get("pin_hash")]
    return {
        "ok": True,
        "sesiones_activas": get_active_sessions_count(),
        "roles_configurados": roles_configurados,
        "roles_totales": list(ROLES_DB.keys())
    }


@app.get("/health")
async def health():
    return {"status": "ok", "motor": "auth", "version": "3.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AUTH_PORT", 8006))
    uvicorn.run("motor_auth:app", host="0.0.0.0", port=port, reload=True)

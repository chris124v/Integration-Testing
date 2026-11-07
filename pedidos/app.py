"""Servicio Pedidos: registra pedidos y cobra cada uno mediante el servicio Pagos.

Variables de entorno:
  PAGOS_URL      URL base del servicio Pagos (obligatoria en Docker).
  DB_PATH        Ruta del archivo SQLite (por defecto ./data/pedidos.db).
  RESET_DB       "true" para borrar la base al arrancar (base nueva en cada corrida).
  PAGOS_TIMEOUT  Segundos de espera maxima a Pagos (por defecto 5).
"""
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

ESQUEMA = """
CREATE TABLE IF NOT EXISTS pedidos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     TEXT    NOT NULL,
    costo       REAL    NOT NULL,
    estado_pago TEXT    NOT NULL CHECK (estado_pago IN ('APROBADO', 'RECHAZADO', 'ERROR')),
    detalle     TEXT,
    creado_en   TEXT    NOT NULL
)
"""


def preparar_base(db_path: str, reiniciar: bool) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    if reiniciar and os.path.exists(db_path):
        os.remove(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(ESQUEMA)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_path = os.getenv("DB_PATH", "./data/pedidos.db")
    preparar_base(app.state.db_path, os.getenv("RESET_DB", "false").lower() == "true")
    app.state.pagos = httpx.Client(
        base_url=os.getenv("PAGOS_URL", "http://localhost:8001"),
        timeout=float(os.getenv("PAGOS_TIMEOUT", "5")),
    )
    yield
    app.state.pagos.close()


app = FastAPI(title="Pedidos", lifespan=lifespan)


class NuevoPedido(BaseModel):
    usuario: str = Field(min_length=1, max_length=80)
    costo: float = Field(gt=0)
    tarjeta: str = Field(pattern=r"^\d{4}$")


def cobrar(cliente: httpx.Client, monto: float, tarjeta: str) -> tuple[str, str]:
    """Llama a Pagos y traduce su respuesta a (estado_pago, detalle)."""
    try:
        respuesta = cliente.post("/pagos", json={"monto": monto, "tarjeta": tarjeta})
    except httpx.RequestError as exc:
        return "ERROR", f"Pagos no disponible: {exc.__class__.__name__}"
    if respuesta.status_code >= 500:
        return "ERROR", f"Pagos respondió HTTP {respuesta.status_code}"
    if respuesta.status_code != 200:
        return "ERROR", f"Respuesta inesperada de Pagos: HTTP {respuesta.status_code}"
    cuerpo = respuesta.json()
    if cuerpo.get("estado") == "APROBADO":
        return "APROBADO", f"Autorización {cuerpo.get('autorizacion', '')}".strip()
    if cuerpo.get("estado") == "RECHAZADO":
        return "RECHAZADO", cuerpo.get("motivo", "Rechazado por la pasarela")
    return "ERROR", "Estado de pago desconocido"


def fila_a_dict(fila: sqlite3.Row) -> dict:
    return dict(fila)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pedidos", status_code=201)
def crear_pedido(pedido: NuevoPedido, request: Request):
    estado, detalle = cobrar(request.app.state.pagos, pedido.costo, pedido.tarjeta)
    creado_en = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(request.app.state.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "INSERT INTO pedidos (usuario, costo, estado_pago, detalle, creado_en) "
            "VALUES (?, ?, ?, ?, ?)",
            (pedido.usuario, pedido.costo, estado, detalle, creado_en),
        )
        fila = conn.execute("SELECT * FROM pedidos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return fila_a_dict(fila)


@app.get("/pedidos")
def listar_pedidos(request: Request):
    with sqlite3.connect(request.app.state.db_path) as conn:
        conn.row_factory = sqlite3.Row
        filas = conn.execute("SELECT * FROM pedidos ORDER BY id DESC").fetchall()
    return [fila_a_dict(f) for f in filas]


@app.get("/pedidos/{pedido_id}")
def obtener_pedido(pedido_id: int, request: Request):
    with sqlite3.connect(request.app.state.db_path) as conn:
        conn.row_factory = sqlite3.Row
        fila = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return fila_a_dict(fila)

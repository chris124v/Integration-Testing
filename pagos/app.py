"""Servicio Pagos: simula una pasarela de pago externa.

Reglas de la simulacion (definidas para el taller):
  - tarjeta 5500 -> pago APROBADO (HTTP 200)
  - tarjeta 0000 -> pago RECHAZADO (HTTP 200, es una respuesta de negocio)
  - tarjeta 9999 -> error interno de la pasarela (HTTP 500)
  - cualquier otra tarjeta de 4 digitos -> RECHAZADO por tarjeta no reconocida
"""
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

TARJETA_APROBADA = "5500"
TARJETA_RECHAZADA = "0000"
TARJETA_ERROR = "9999"

app = FastAPI(title="Pagos - pasarela simulada")


class SolicitudPago(BaseModel):
    monto: float = Field(gt=0)
    tarjeta: str = Field(pattern=r"^\d{4}$")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pagos")
def procesar_pago(solicitud: SolicitudPago):
    if solicitud.tarjeta == TARJETA_ERROR:
        raise HTTPException(status_code=500, detail="Error interno de la pasarela")
    if solicitud.tarjeta == TARJETA_APROBADA:
        return {"estado": "APROBADO", "autorizacion": uuid.uuid4().hex[:8].upper()}
    if solicitud.tarjeta == TARJETA_RECHAZADA:
        return {"estado": "RECHAZADO", "motivo": "Fondos insuficientes"}
    return {"estado": "RECHAZADO", "motivo": "Tarjeta no reconocida"}

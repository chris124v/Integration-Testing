"""Pruebas de integracion ESTRECHAS (Fowler, 2018) del servicio Pedidos.

Pedidos se prueba con su base SQLite real (temporal), pero el servicio Pagos se
reemplaza por un doble de prueba (httpx.MockTransport). Asi se verifica que
Pedidos interpreta cada respuesta posible de la pasarela sin levantarla.
"""
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

import app as pedidos_app


def doble_de_pagos(respuesta_o_excepcion):
    def manejador(request: httpx.Request) -> httpx.Response:
        if isinstance(respuesta_o_excepcion, Exception):
            raise respuesta_o_excepcion
        return respuesta_o_excepcion
    return httpx.Client(base_url="http://pagos-falso", transport=httpx.MockTransport(manejador))


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "pedidos.db"))
    monkeypatch.setenv("RESET_DB", "true")
    with TestClient(pedidos_app.app) as c:
        yield c


def estado_en_base(cliente, pedido_id):
    with sqlite3.connect(cliente.app.state.db_path) as conn:
        return conn.execute("SELECT estado_pago FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()[0]


@pytest.mark.parametrize(
    "respuesta_pagos, estado_esperado",
    [
        (httpx.Response(200, json={"estado": "APROBADO", "autorizacion": "AB12CD34"}), "APROBADO"),
        (httpx.Response(200, json={"estado": "RECHAZADO", "motivo": "Fondos insuficientes"}), "RECHAZADO"),
        (httpx.Response(500, json={"detail": "Error interno"}), "ERROR"),
        (httpx.ConnectError("sin conexion"), "ERROR"),
        (httpx.ReadTimeout("tiempo agotado"), "ERROR"),
    ],
    ids=["aprobado", "rechazado", "pagos-500", "pagos-caido", "pagos-timeout"],
)
def test_pedido_guarda_el_estado_del_pago(cliente, respuesta_pagos, estado_esperado):
    cliente.app.state.pagos = doble_de_pagos(respuesta_pagos)

    r = cliente.post("/pedidos", json={"usuario": "Ana", "costo": 1500, "tarjeta": "1234"})

    assert r.status_code == 201
    assert r.json()["estado_pago"] == estado_esperado
    assert estado_en_base(cliente, r.json()["id"]) == estado_esperado


def test_datos_invalidos_no_llegan_a_pagos(cliente):
    llamadas = []

    def manejador(request):
        llamadas.append(request)
        return httpx.Response(200, json={"estado": "APROBADO"})

    cliente.app.state.pagos = httpx.Client(base_url="http://x", transport=httpx.MockTransport(manejador))
    r = cliente.post("/pedidos", json={"usuario": "", "costo": -5, "tarjeta": "12"})

    assert r.status_code == 422
    assert llamadas == []


# ---------------------------------------------------------------------------
# PRÁCTICA (CP-17 a CP-20). Reemplace cada pytest.skip por la prueba.
# Use como guía las pruebas de arriba: doble_de_pagos, la fixture cliente y
# estado_en_base ya están disponibles.
# ---------------------------------------------------------------------------

def test_cp17_estado_desconocido_de_pagos(cliente):
    """CP-17 (fácil). El doble de Pagos responde HTTP 200 con {"estado": "PENDIENTE"}.

    Esperado: Pedidos responde 201, estado_pago = ERROR, detalle =
    "Estado de pago desconocido", y SQLite guarda ERROR.
    """
    pytest.skip("Ejercicio CP-17 pendiente")


def test_cp18_codigo_inesperado_de_pagos(cliente):
    """CP-18 (fácil). El doble de Pagos responde HTTP 404 y luego HTTP 422.

    Recorra ambos códigos dentro de la misma prueba. Esperado en cada uno:
    201, estado_pago = ERROR y detalle = "Respuesta inesperada de Pagos: HTTP <código>".
    """
    pytest.skip("Ejercicio CP-18 pendiente")


def test_cp19_rechazo_sin_motivo(cliente):
    """CP-19 (fácil). El doble responde HTTP 200 con {"estado": "RECHAZADO"} sin campo "motivo".

    Esperado: 201, estado_pago = RECHAZADO y detalle = "Rechazado por la pasarela".
    """
    pytest.skip("Ejercicio CP-19 pendiente")


def test_cp20_solicitud_que_pedidos_envia_a_pagos(cliente):
    """CP-20 (medio). Contrato visto desde el consumidor.

    Cree un doble que guarde cada solicitud recibida (como en
    test_datos_invalidos_no_llegan_a_pagos) y cree un pedido con costo 1500 y tarjeta "1234".
    Esperado: exactamente 1 llamada, método POST, ruta /pagos y cuerpo JSON
    {"monto": 1500, "tarjeta": "1234"}.
    Pista: el cuerpo de la solicitud está en request.content (use json.loads).
    """
    pytest.skip("Ejercicio CP-20 pendiente")

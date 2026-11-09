"""SOLUCIÓN de referencia de pedidos/tests/test_pedidos_estrecha.py (CP-01 a CP-06 + práctica CP-17 a CP-20).

Pruebas de integracion ESTRECHAS (Fowler, 2018) del servicio Pedidos.
Pedidos se prueba con su base SQLite real (temporal), pero el servicio Pagos se
reemplaza por un doble de prueba (httpx.MockTransport).
"""
import json
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
# PRÁCTICA (CP-17 a CP-20), resuelta.
# ---------------------------------------------------------------------------

def crear_pedido(cliente):
    return cliente.post("/pedidos", json={"usuario": "Ana", "costo": 1500, "tarjeta": "1234"})


def test_cp17_estado_desconocido_de_pagos(cliente):
    cliente.app.state.pagos = doble_de_pagos(httpx.Response(200, json={"estado": "PENDIENTE"}))

    r = crear_pedido(cliente)

    assert r.status_code == 201
    assert r.json()["estado_pago"] == "ERROR"
    assert r.json()["detalle"] == "Estado de pago desconocido"
    assert estado_en_base(cliente, r.json()["id"]) == "ERROR"


def test_cp18_codigo_inesperado_de_pagos(cliente):
    for codigo in (404, 422):
        cliente.app.state.pagos = doble_de_pagos(httpx.Response(codigo, json={"detail": "x"}))

        r = crear_pedido(cliente)

        assert r.status_code == 201
        assert r.json()["estado_pago"] == "ERROR"
        assert r.json()["detalle"] == f"Respuesta inesperada de Pagos: HTTP {codigo}"
        assert estado_en_base(cliente, r.json()["id"]) == "ERROR"


def test_cp19_rechazo_sin_motivo(cliente):
    cliente.app.state.pagos = doble_de_pagos(httpx.Response(200, json={"estado": "RECHAZADO"}))

    r = crear_pedido(cliente)

    assert r.status_code == 201
    assert r.json()["estado_pago"] == "RECHAZADO"
    assert r.json()["detalle"] == "Rechazado por la pasarela"
    assert estado_en_base(cliente, r.json()["id"]) == "RECHAZADO"


def test_cp20_solicitud_que_pedidos_envia_a_pagos(cliente):
    llamadas = []

    def manejador(request):
        llamadas.append(request)
        return httpx.Response(200, json={"estado": "APROBADO", "autorizacion": "AB12CD34"})

    cliente.app.state.pagos = httpx.Client(base_url="http://x", transport=httpx.MockTransport(manejador))

    r = crear_pedido(cliente)

    assert r.status_code == 201
    assert len(llamadas) == 1
    solicitud = llamadas[0]
    assert solicitud.method == "POST"
    assert solicitud.url.path == "/pagos"
    assert json.loads(solicitud.content) == {"monto": 1500, "tarjeta": "1234"}

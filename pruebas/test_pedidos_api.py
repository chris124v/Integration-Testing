"""Pedidos + Pagos + SQLite reales, sin interfaz grafica."""
import uuid

import pytest


@pytest.mark.parametrize(
    "tarjeta, estado_esperado",
    [("5500", "APROBADO"), ("0000", "RECHAZADO"), ("9999", "ERROR")],
    ids=["aprobado", "rechazado", "error"],
)
def test_pedido_se_guarda_con_el_estado_del_pago(api_pedidos, consultar_bd, tarjeta, estado_esperado):
    usuario = f"api-{estado_esperado.lower()}-{uuid.uuid4().hex[:6]}"

    r = api_pedidos.post("/pedidos", data={"usuario": usuario, "costo": 1800, "tarjeta": tarjeta})

    assert r.status == 201
    pedido = r.json()
    assert pedido["estado_pago"] == estado_esperado

    fila = consultar_bd("SELECT * FROM pedidos WHERE id = ?", (pedido["id"],))
    assert fila is not None, "El pedido no quedo guardado en SQLite"
    assert fila["usuario"] == usuario
    assert fila["estado_pago"] == estado_esperado

    assert api_pedidos.get(f"/pedidos/{pedido['id']}").json()["estado_pago"] == estado_esperado

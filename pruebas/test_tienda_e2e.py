"""Flujo completo desde el navegador: Frontend -> Pedidos -> Pagos -> SQLite."""
import uuid

import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize(
    "tarjeta, estado_esperado",
    [("5500", "APROBADO"), ("0000", "RECHAZADO"), ("9999", "ERROR")],
    ids=["aprobado", "rechazado", "error"],
)
def test_crear_pedido_desde_la_tienda(page, consultar_bd, capturar, tarjeta, estado_esperado):
    usuario = f"ui-{estado_esperado.lower()}-{uuid.uuid4().hex[:6]}"

    page.goto("/")
    page.get_by_test_id("btn-crear-pedido").click()
    page.get_by_test_id("input-usuario").fill(usuario)
    page.get_by_test_id("input-costo").fill("2500")
    page.get_by_test_id("input-tarjeta").fill(tarjeta)
    capturar("formulario")
    page.get_by_test_id("btn-enviar").click()

    expect(page.get_by_test_id("mensaje")).to_contain_text(estado_esperado)
    fila = page.get_by_role("row").filter(has_text=usuario)
    expect(fila.get_by_test_id("estado-pago")).to_have_text(estado_esperado)
    capturar("resultado")

    registro = consultar_bd("SELECT * FROM pedidos WHERE usuario = ?", (usuario,))
    assert registro is not None, "El pedido no quedo guardado en SQLite"
    assert registro["estado_pago"] == estado_esperado
    assert registro["costo"] == 2500

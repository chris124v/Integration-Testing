# SOLUCIÓN de referencia de pruebas/test_tienda_e2e.py: copie este archivo sobre el original para ejecutarlo.
"""Flujo completo desde el navegador: Frontend -> Pedidos -> Pagos -> SQLite.

Playwright abre la tienda en Chromium, llena el formulario como lo haría un
usuario y revisa la pantalla. Al final se consulta SQLite para confirmar que lo
que se ve coincide con lo guardado. Estas pruebas generan capturas y video.
"""
import uuid

import pytest
from playwright.sync_api import expect


# --- CP-14 a CP-16 -------------------------------------------------------------
# Una prueba que se ejecuta 3 veces, una por tarjeta, creando el pedido desde la tienda:
#   CP-14 5500 -> mensaje y fila con APROBADO
#   CP-15 0000 -> mensaje y fila con RECHAZADO
#   CP-16 9999 -> mensaje y fila con ERROR
# En los tres casos, el pedido debe quedar en SQLite con el mismo estado.
@pytest.mark.parametrize(
    "tarjeta, estado_esperado",
    [("5500", "APROBADO"), ("0000", "RECHAZADO"), ("9999", "ERROR")],
    ids=["aprobado", "rechazado", "error"],
)
def test_crear_pedido_desde_la_tienda(page, consultar_bd, capturar, tarjeta, estado_esperado):
    usuario = f"ui-{estado_esperado.lower()}-{uuid.uuid4().hex[:6]}"

    # Abrir la tienda, pulsar «Crear pedido» y llenar el formulario.
    # Los elementos se buscan por su atributo data-testid (ver frontend/public/index.html).
    page.goto("/")
    page.get_by_test_id("btn-crear-pedido").click()
    page.get_by_test_id("input-usuario").fill(usuario)
    page.get_by_test_id("input-costo").fill("2500")
    page.get_by_test_id("input-tarjeta").fill(tarjeta)
    capturar("formulario")  # foto antes de enviar
    page.get_by_test_id("btn-enviar").click()

    # expect(...) espera a que la página se actualice; no hace falta poner pausas.
    expect(page.get_by_test_id("mensaje")).to_contain_text(estado_esperado)
    fila = page.get_by_role("row").filter(has_text=usuario)  # la fila de la tabla de este pedido
    expect(fila.get_by_test_id("estado-pago")).to_have_text(estado_esperado)
    capturar("resultado")  # foto con el resultado

    # Lo que se ve en pantalla debe coincidir con lo guardado en SQLite.
    registro = consultar_bd("SELECT * FROM pedidos WHERE usuario = ?", (usuario,))
    assert registro is not None, "El pedido no quedo guardado en SQLite"
    assert registro["estado_pago"] == estado_esperado
    assert registro["costo"] == 2500


# ---------------------------------------------------------------------------
# PRÁCTICA (CP-29 a CP-32), resuelta.
# ---------------------------------------------------------------------------

def crear_desde_la_tienda(page, tarjeta, costo="2500"):
    """Llena y envía el formulario; devuelve el usuario y la fila de la tabla."""
    usuario = f"ui-{uuid.uuid4().hex[:6]}"
    page.goto("/")
    page.get_by_test_id("btn-crear-pedido").click()
    page.get_by_test_id("input-usuario").fill(usuario)
    page.get_by_test_id("input-costo").fill(costo)
    page.get_by_test_id("input-tarjeta").fill(tarjeta)
    page.get_by_test_id("btn-enviar").click()
    return usuario, page.get_by_role("row").filter(has_text=usuario)


def test_cp29_tarjeta_no_reconocida_desde_la_tienda(page, consultar_bd, capturar):
    usuario, fila = crear_desde_la_tienda(page, "1234")

    expect(page.get_by_test_id("mensaje")).to_contain_text("RECHAZADO (Tarjeta no reconocida)")
    expect(fila.get_by_test_id("estado-pago")).to_have_text("RECHAZADO")
    capturar("resultado")

    registro = consultar_bd("SELECT * FROM pedidos WHERE usuario = ?", (usuario,))
    assert registro is not None
    assert registro["estado_pago"] == "RECHAZADO"


def test_cp30_la_fila_coincide_con_la_base(page, consultar_bd):
    usuario, fila = crear_desde_la_tienda(page, "0000", costo="1234.5")
    expect(fila.get_by_test_id("estado-pago")).to_have_text("RECHAZADO")

    registro = consultar_bd("SELECT * FROM pedidos WHERE usuario = ?", (usuario,))
    celdas = fila.get_by_role("cell")
    expect(celdas.nth(1)).to_have_text(registro["usuario"])
    expect(celdas.nth(2)).to_have_text(f"{registro['costo']:.2f}")
    expect(celdas.nth(3)).to_have_text(registro["estado_pago"])
    expect(celdas.nth(4)).to_have_text(registro["detalle"])


def test_cp31_el_pedido_sigue_al_recargar(page):
    _, fila = crear_desde_la_tienda(page, "5500")
    expect(fila.get_by_test_id("estado-pago")).to_have_text("APROBADO")

    page.reload()

    expect(fila.get_by_test_id("estado-pago")).to_have_text("APROBADO")
    expect(page.get_by_test_id("sin-pedidos")).to_be_hidden()


def test_cp32_el_proxy_reenvia_sin_alterar(api_tienda, consultar_bd):
    usuario = f"proxy-{uuid.uuid4().hex[:6]}"
    r = api_tienda.post("/api/pedidos", data={"usuario": usuario, "costo": 1000, "tarjeta": "5500"})
    assert r.status == 201
    assert r.json()["estado_pago"] == "APROBADO"
    assert consultar_bd("SELECT * FROM pedidos WHERE usuario = ?", (usuario,)) is not None

    r = api_tienda.post("/api/pedidos", data={"usuario": f"proxy-{uuid.uuid4().hex[:6]}", "costo": 1000, "tarjeta": "55"})
    assert r.status == 422

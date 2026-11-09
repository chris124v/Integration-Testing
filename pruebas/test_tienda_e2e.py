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
# PRÁCTICA (CP-29 a CP-32). Reemplace cada pytest.skip por la prueba.
# Use como guía la prueba de arriba (page, consultar_bd y capturar).
# ---------------------------------------------------------------------------

def test_cp29_tarjeta_no_reconocida_desde_la_tienda(page, consultar_bd, capturar):
    """CP-29 (fácil). Cree un pedido desde la tienda con la tarjeta 1234.

    Esperado: mensaje con "RECHAZADO (Tarjeta no reconocida)", fila con
    RECHAZADO y registro en SQLite con ese estado.
    """
    pytest.skip("Ejercicio CP-29 pendiente")


def test_cp30_la_fila_coincide_con_la_base(page, consultar_bd):
    """CP-30 (fácil). Cree un pedido desde la tienda y lea su fila en la tabla.

    Esperado: la fila muestra el usuario, el costo con dos decimales, el estado
    y el detalle, y todo coincide con el registro de SQLite.
    """
    pytest.skip("Ejercicio CP-30 pendiente")


def test_cp31_el_pedido_sigue_al_recargar(page):
    """CP-31 (fácil). Cree un pedido desde la tienda y recargue la página con page.reload().

    Esperado: la fila sigue en la tabla con su estado y el texto
    "Todavía no hay pedidos." (data-testid "sin-pedidos") está oculto.
    """
    pytest.skip("Ejercicio CP-31 pendiente")


def test_cp32_el_proxy_reenvia_sin_alterar(api_tienda, consultar_bd):
    """CP-32 (medio). Use la fixture api_tienda, que habla con http://localhost:8080 (nginx).

    Envíe POST /api/pedidos con tarjeta 5500 y otro con tarjeta "55".
    Esperado: 201 con APROBADO (y registro en SQLite) y 422; el proxy no altera
    los códigos de Pedidos.
    """
    pytest.skip("Ejercicio CP-32 pendiente")

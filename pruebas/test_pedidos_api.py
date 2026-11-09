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


# ---------------------------------------------------------------------------
# PRÁCTICA (CP-25 a CP-28). Reemplace cada pytest.skip por la prueba.
# Use como guía la prueba de arriba (api_pedidos y consultar_bd).
# ---------------------------------------------------------------------------

def test_cp25_el_detalle_se_guarda_igual(api_pedidos, consultar_bd):
    """CP-25 (fácil). Con las tarjetas 5500, 0000 y 9999 (recorridas dentro de la prueba).

    Esperado: el "detalle" de la respuesta es igual al de SQLite, y vale:
    5500 -> empieza con "Autorización "; 0000 -> "Fondos insuficientes";
    9999 -> "Pagos respondió HTTP 500".
    """
    pytest.skip("Ejercicio CP-25 pendiente")


def test_cp26_el_costo_con_decimales_llega_intacto(api_pedidos, consultar_bd):
    """CP-26 (fácil). Cree un pedido con costo 2500.75.

    Esperado: 2500.75 en la respuesta, en GET /pedidos/{id} y en SQLite
    (sin redondeo ni conversión a entero).
    """
    pytest.skip("Ejercicio CP-26 pendiente")


def test_cp27_datos_invalidos_no_se_guardan(api_pedidos, consultar_bd):
    """CP-27 (fácil). Envíe un pedido con costo 0 y otro con tarjeta "12", cada uno con un usuario único.

    Esperado: HTTP 422 en ambos y ningún registro en SQLite para esos usuarios.
    """
    pytest.skip("Ejercicio CP-27 pendiente")


def test_cp28_el_listado_trae_lo_mas_reciente_primero(api_pedidos):
    """CP-28 (medio). Cree dos pedidos seguidos y luego llame a GET /pedidos.

    Esperado: HTTP 200, aparecen ambos y el segundo creado va antes que el primero.
    Ojo: la base ya tiene pedidos de otras pruebas; compare posiciones relativas,
    no el tamaño de la lista.
    """
    pytest.skip("Ejercicio CP-28 pendiente")

# SOLUCIÓN de referencia de pruebas/test_pedidos_api.py: copie este archivo sobre el original para ejecutarlo.
"""Pedidos + Pagos + SQLite reales, sin interfaz grafica.

Aquí no hay dobles: Pedidos llama al Pagos real dentro de Docker y escribe en la
base real. Cada prueba verifica el resultado en tres lugares: la respuesta de
Pedidos, el archivo SQLite y la consulta GET de Pedidos.
"""
import uuid

import pytest


# --- CP-11 a CP-13 -------------------------------------------------------------
# Una prueba que se ejecuta 3 veces, una por tarjeta, creando un pedido en Pedidos:
#   CP-11 5500 -> 201 y APROBADO
#   CP-12 0000 -> 201 y RECHAZADO
#   CP-13 9999 -> 201 y ERROR (Pagos respondió 500, pero el pedido igual se guarda)
@pytest.mark.parametrize(
    "tarjeta, estado_esperado",
    [("5500", "APROBADO"), ("0000", "RECHAZADO"), ("9999", "ERROR")],
    ids=["aprobado", "rechazado", "error"],
)
def test_pedido_se_guarda_con_el_estado_del_pago(api_pedidos, consultar_bd, tarjeta, estado_esperado):
    # Usuario único (sufijo aleatorio) para encontrar este pedido sin depender de otras pruebas.
    usuario = f"api-{estado_esperado.lower()}-{uuid.uuid4().hex[:6]}"

    # 1) La respuesta de Pedidos.
    r = api_pedidos.post("/pedidos", data={"usuario": usuario, "costo": 1800, "tarjeta": tarjeta})

    assert r.status == 201
    pedido = r.json()
    assert pedido["estado_pago"] == estado_esperado

    # 2) Lo que quedó guardado en SQLite (leído directamente del archivo).
    fila = consultar_bd("SELECT * FROM pedidos WHERE id = ?", (pedido["id"],))
    assert fila is not None, "El pedido no quedo guardado en SQLite"
    assert fila["usuario"] == usuario
    assert fila["estado_pago"] == estado_esperado

    # 3) Lo que devuelve Pedidos al consultar ese pedido por su id.
    assert api_pedidos.get(f"/pedidos/{pedido['id']}").json()["estado_pago"] == estado_esperado


# ---------------------------------------------------------------------------
# PRÁCTICA (CP-25 a CP-28), resuelta.
# ---------------------------------------------------------------------------

def nuevo_usuario(prefijo):
    return f"{prefijo}-{uuid.uuid4().hex[:6]}"


def test_cp25_el_detalle_se_guarda_igual(api_pedidos, consultar_bd):
    casos = {
        "5500": lambda d: d.startswith("Autorización "),
        "0000": lambda d: d == "Fondos insuficientes",
        "9999": lambda d: d == "Pagos respondió HTTP 500",
    }
    for tarjeta, detalle_correcto in casos.items():
        r = api_pedidos.post("/pedidos", data={"usuario": nuevo_usuario("det"), "costo": 1000, "tarjeta": tarjeta})
        assert r.status == 201
        pedido = r.json()

        fila = consultar_bd("SELECT * FROM pedidos WHERE id = ?", (pedido["id"],))
        assert fila["detalle"] == pedido["detalle"]
        assert detalle_correcto(pedido["detalle"]), f"{tarjeta}: detalle inesperado {pedido['detalle']!r}"


def test_cp26_el_costo_con_decimales_llega_intacto(api_pedidos, consultar_bd):
    r = api_pedidos.post("/pedidos", data={"usuario": nuevo_usuario("dec"), "costo": 2500.75, "tarjeta": "5500"})

    assert r.status == 201
    pedido = r.json()
    assert pedido["costo"] == 2500.75
    assert api_pedidos.get(f"/pedidos/{pedido['id']}").json()["costo"] == 2500.75
    assert consultar_bd("SELECT costo FROM pedidos WHERE id = ?", (pedido["id"],))["costo"] == 2500.75


def test_cp27_datos_invalidos_no_se_guardan(api_pedidos, consultar_bd):
    for costo, tarjeta in ((0, "5500"), (1000, "12")):
        usuario = nuevo_usuario("inv")
        r = api_pedidos.post("/pedidos", data={"usuario": usuario, "costo": costo, "tarjeta": tarjeta})

        assert r.status == 422
        assert consultar_bd("SELECT * FROM pedidos WHERE usuario = ?", (usuario,)) is None


def test_cp28_el_listado_trae_lo_mas_reciente_primero(api_pedidos):
    ids = []
    for _ in range(2):
        r = api_pedidos.post("/pedidos", data={"usuario": nuevo_usuario("orden"), "costo": 1000, "tarjeta": "5500"})
        ids.append(r.json()["id"])

    r = api_pedidos.get("/pedidos")
    assert r.status == 200
    listado = [p["id"] for p in r.json()]

    assert ids[0] in listado and ids[1] in listado
    assert listado.index(ids[1]) < listado.index(ids[0])

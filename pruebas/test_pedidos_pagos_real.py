"""SOLUCIÓN de referencia de pruebas/test_pedidos_pagos_real.py (práctica CP-21 a CP-24).

Pedidos + Pagos reales: lo que Pagos responde debe llegar bien traducido a Pedidos.
"""
import uuid


def nuevo_usuario(prefijo):
    return f"{prefijo}-{uuid.uuid4().hex[:6]}"


def crear_pedido(api_pedidos, tarjeta, costo=1000):
    r = api_pedidos.post("/pedidos", data={"usuario": nuevo_usuario("real"), "costo": costo, "tarjeta": tarjeta})
    assert r.status == 201
    return r.json()


def test_cp21_cada_cobro_se_registra_por_separado(api_pedidos, consultar_bd):
    primero = crear_pedido(api_pedidos, "5500")
    segundo = crear_pedido(api_pedidos, "5500")

    assert primero["id"] != segundo["id"]
    assert primero["detalle"] != segundo["detalle"]
    for pedido in (primero, segundo):
        fila = consultar_bd("SELECT * FROM pedidos WHERE id = ?", (pedido["id"],))
        assert fila is not None
        assert fila["estado_pago"] == "APROBADO"
        assert fila["detalle"] == pedido["detalle"]
        assert fila["detalle"].startswith("Autorización ")


def test_cp22_los_tres_estados_conviven(api_pedidos):
    esperados = {}
    for tarjeta, estado in (("5500", "APROBADO"), ("0000", "RECHAZADO"), ("9999", "ERROR")):
        esperados[crear_pedido(api_pedidos, tarjeta)["id"]] = estado

    r = api_pedidos.get("/pedidos")
    assert r.status == 200
    listado = {p["id"]: p["estado_pago"] for p in r.json()}

    for pedido_id, estado in esperados.items():
        assert listado[pedido_id] == estado


def test_cp23_un_rechazo_no_es_un_error(api_pagos, api_pedidos):
    for tarjeta, http_pagos, estado in (("0000", 200, "RECHAZADO"), ("9999", 500, "ERROR")):
        pagos = api_pagos.post("/pagos", data={"monto": 1000, "tarjeta": tarjeta})
        assert pagos.status == http_pagos

        pedido = crear_pedido(api_pedidos, tarjeta)  # verifica que Pedidos responde 201
        assert pedido["estado_pago"] == estado


def test_cp24_pedidos_traduce_lo_que_responde_pagos(api_pagos, api_pedidos):
    for tarjeta in ("5500", "0000", "1234", "9999"):
        pagos = api_pagos.post("/pagos", data={"monto": 1000, "tarjeta": tarjeta})
        pedido = crear_pedido(api_pedidos, tarjeta)

        if pagos.status >= 500:
            assert pedido["estado_pago"] == "ERROR"
            assert pedido["detalle"] == f"Pagos respondió HTTP {pagos.status}"
            continue

        cuerpo = pagos.json()
        assert pedido["estado_pago"] == cuerpo["estado"]
        if cuerpo["estado"] == "APROBADO":
            assert pedido["detalle"].startswith("Autorización ")
        else:
            assert pedido["detalle"] == cuerpo["motivo"]

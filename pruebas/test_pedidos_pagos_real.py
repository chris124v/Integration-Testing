"""Pedidos + Pagos reales: lo que Pagos responde debe llegar bien traducido a Pedidos.

PRÁCTICA (CP-21 a CP-24). Reemplace cada pytest.skip por la prueba.
Fixtures disponibles (conftest.py): api_pagos, api_pedidos y consultar_bd.
Use usuarios únicos (por ejemplo con uuid) para no depender de otras pruebas.
"""
import pytest


def test_cp21_cada_cobro_se_registra_por_separado(api_pedidos, consultar_bd):
    """CP-21 (fácil). Cree dos pedidos seguidos con tarjeta 5500.

    Esperado: ids distintos, los dos guardados en SQLite con APROBADO, y dos
    detalles "Autorización XXXXXXXX" con códigos diferentes.
    """
    pytest.skip("Ejercicio CP-21 pendiente")


def test_cp22_los_tres_estados_conviven(api_pedidos):
    """CP-22 (fácil). Cree un pedido con 5500, otro con 0000 y otro con 9999; luego GET /pedidos.

    Esperado: los tres aparecen en el listado, cada uno con su estado
    (APROBADO, RECHAZADO y ERROR), sin mezclarse.
    """
    pytest.skip("Ejercicio CP-22 pendiente")


def test_cp23_un_rechazo_no_es_un_error(api_pagos, api_pedidos):
    """CP-23 (fácil). Con las tarjetas 0000 y 9999, llame primero a Pagos directo y luego a Pedidos.

    Esperado: Pagos responde 200 (rechazo) y 500 (error); Pedidos responde 201
    en ambos casos, con RECHAZADO y ERROR respectivamente.
    """
    pytest.skip("Ejercicio CP-23 pendiente")


def test_cp24_pedidos_traduce_lo_que_responde_pagos(api_pagos, api_pedidos):
    """CP-24 (medio). Con las tarjetas 5500, 0000, 1234 y 9999: llame a Pagos directo y luego cree el pedido.

    Esperado: el estado de Pedidos es la traducción de lo que respondió Pagos:
      - Pagos 200 con APROBADO  -> APROBADO y detalle que empieza con "Autorización ".
      - Pagos 200 con RECHAZADO -> RECHAZADO y detalle igual al "motivo" de Pagos.
      - Pagos con código 5xx    -> ERROR y detalle "Pagos respondió HTTP <código>".
    """
    pytest.skip("Ejercicio CP-24 pendiente")

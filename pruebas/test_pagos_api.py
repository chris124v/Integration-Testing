"""Pagos aislado: verifica el contrato de la pasarela simulada.

Es el primer paso de la estrategia ascendente: antes de probar a Pedidos con Pagos,
se confirma que Pagos responde lo que Pedidos espera (códigos y cuerpos). Si este
contrato cambia, las pruebas de este archivo son las primeras en avisar.
"""
import pytest


# --- CP-07 a CP-09 -------------------------------------------------------------
# Una prueba que se ejecuta 3 veces, una por tarjeta, llamando a Pagos directamente:
#   CP-07 5500 -> HTTP 200 y estado APROBADO
#   CP-08 0000 -> HTTP 200 y estado RECHAZADO  (un rechazo es una respuesta normal, no un error)
#   CP-09 9999 -> HTTP 500                      (error interno de la pasarela; no hay cuerpo que revisar)
@pytest.mark.parametrize(
    "tarjeta, http_esperado, estado_esperado",
    [("5500", 200, "APROBADO"), ("0000", 200, "RECHAZADO"), ("9999", 500, None)],
    ids=["aprobado", "rechazado", "error-500"],
)
def test_respuestas_de_la_pasarela(api_pagos, tarjeta, http_esperado, estado_esperado):
    r = api_pagos.post("/pagos", data={"monto": 1000, "tarjeta": tarjeta})

    assert r.status == http_esperado
    if estado_esperado:  # solo las respuestas 200 traen un "estado" en el cuerpo
        assert r.json()["estado"] == estado_esperado


# --- CP-10 ----------------------------------------------------------------------
# Una tarjeta que no tiene 4 dígitos es rechazada por la validación de Pagos con 422.
def test_tarjeta_con_formato_invalido_se_rechaza_con_422(api_pagos):
    r = api_pagos.post("/pagos", data={"monto": 1000, "tarjeta": "55"})
    assert r.status == 422

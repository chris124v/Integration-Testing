"""Pagos aislado: verifica el contrato de la pasarela simulada."""
import pytest


@pytest.mark.parametrize(
    "tarjeta, http_esperado, estado_esperado",
    [("5500", 200, "APROBADO"), ("0000", 200, "RECHAZADO"), ("9999", 500, None)],
    ids=["aprobado", "rechazado", "error-500"],
)
def test_respuestas_de_la_pasarela(api_pagos, tarjeta, http_esperado, estado_esperado):
    r = api_pagos.post("/pagos", data={"monto": 1000, "tarjeta": tarjeta})

    assert r.status == http_esperado
    if estado_esperado:
        assert r.json()["estado"] == estado_esperado


def test_tarjeta_con_formato_invalido_se_rechaza_con_422(api_pagos):
    r = api_pagos.post("/pagos", data={"monto": 1000, "tarjeta": "55"})
    assert r.status == 422

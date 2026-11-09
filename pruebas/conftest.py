"""Configuracion de las pruebas de integracion AMPLIAS (Fowler, 2018).

Todas las pruebas de esta carpeta usan los tres contenedores reales levantados
con docker compose. Las URL y la ruta de la base se pueden cambiar por entorno.

Las fixtures de este archivo están disponibles en todas las pruebas de la carpeta:
basta con ponerlas como parámetro de la función de prueba.
"""
import base64
import os
import sqlite3
from pathlib import Path

import pytest
import pytest_html

# Direcciones de los servicios y de la base. Por defecto apuntan a lo que levanta
# docker compose en la máquina local; GitHub Actions cambia DB_PATH por variable de entorno.
RAIZ = Path(__file__).resolve().parent.parent
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
PEDIDOS_URL = os.getenv("PEDIDOS_URL", "http://localhost:8000")
PAGOS_URL = os.getenv("PAGOS_URL", "http://localhost:8001")
DB_PATH = Path(os.getenv("DB_PATH", RAIZ / "data" / "pedidos.db")).resolve()
CAPTURAS = Path(__file__).resolve().parent / "reporte" / "capturas"


@pytest.fixture(scope="session")
def base_url():
    """URL base del navegador: page.goto("/") abre la tienda (frontend)."""
    return FRONTEND_URL


@pytest.fixture(scope="session")
def api_pagos(playwright):
    """Cliente HTTP que habla directo con Pagos (http://localhost:8001)."""
    contexto = playwright.request.new_context(base_url=PAGOS_URL)
    yield contexto
    contexto.dispose()


@pytest.fixture(scope="session")
def api_pedidos(playwright):
    """Cliente HTTP que habla directo con Pedidos (http://localhost:8000)."""
    contexto = playwright.request.new_context(base_url=PEDIDOS_URL)
    yield contexto
    contexto.dispose()


@pytest.fixture(scope="session")
def api_tienda(playwright):
    """Cliente HTTP que habla con el frontend (nginx), que reenvía /api/* a Pedidos."""
    contexto = playwright.request.new_context(base_url=FRONTEND_URL)
    yield contexto
    contexto.dispose()


@pytest.fixture
def consultar_bd():
    """Lee directamente el archivo SQLite que escribe el contenedor de Pedidos.

    Uso: fila = consultar_bd("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
    Devuelve la primera fila (se accede por nombre de columna, ej. fila["estado_pago"])
    o None si no hay resultados. Abre la base en solo lectura.
    """
    def _consultar(sql, parametros=()):
        assert DB_PATH.exists(), f"No existe la base {DB_PATH}; levante docker compose primero"
        with sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, parametros).fetchone()
    return _consultar


@pytest.fixture
def capturar(page, extras, request):
    """Guarda una captura en reporte/capturas y la incrusta en el reporte HTML.

    Uso: capturar("formulario") toma una foto de la página en ese momento.
    """
    def _capturar(nombre):
        CAPTURAS.mkdir(parents=True, exist_ok=True)
        imagen = page.screenshot(path=CAPTURAS / f"{request.node.name}-{nombre}.png", full_page=True)
        extras.append(pytest_html.extras.png(base64.b64encode(imagen).decode(), name=nombre))
    return _capturar

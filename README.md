# Taller de Pruebas de Integración Automatizadas — Tienda Mínima

Tienda mínima con tres contenedores que se comunican por HTTP:

```
Navegador ──► frontend (nginx, :8080) ──/api──► pedidos (FastAPI, :8000) ──HTTP──► pagos (FastAPI, :8001)
                                                      │
                                                      ▼
                                              SQLite ./data/pedidos.db
```

- **pagos**: simula una pasarela de pago externa. No guarda nada.
- **pedidos**: recibe el pedido, cobra en Pagos (URL en la variable `PAGOS_URL`) y guarda el pedido con el estado del pago en SQLite.
- **frontend**: lista los pedidos y su estado; el botón «Crear pedido» (arriba a la derecha) pide usuario, costo y tarjeta.

## Estructura

```
Src/
├── docker-compose.yml               # levanta pagos, pedidos y frontend
├── .github/workflows/pruebas-integracion.yml
├── pagos/        app.py, Dockerfile, requirements.txt
├── pedidos/      app.py, Dockerfile, requirements*.txt
│   └── tests/    test_pedidos_estrecha.py   # integración ESTRECHA (Pagos reemplazado por un doble)
├── frontend/     Dockerfile, templates/default.conf.template, public/ (index.html, app.js, styles.css)
└── pruebas/      pytest.ini, conftest.py, requirements.txt
    ├── test_pagos_api.py      # Pagos real, aislado
    ├── test_pedidos_api.py    # Pedidos + Pagos + SQLite reales
    └── test_tienda_e2e.py     # Playwright: navegador + 3 contenedores + SQLite
```

## Resultados esperados

| Tarjeta | Respuesta de Pagos | `estado_pago` en Pedidos y SQLite | Mensaje en la tienda | Detalle guardado |
|---|---|---|---|---|
| `5500` | HTTP 200 `{"estado":"APROBADO","autorizacion":"XXXXXXXX"}` | `APROBADO` (verde) | «Pedido #N creado: pago APROBADO» | `Autorización XXXXXXXX` |
| `0000` | HTTP 200 `{"estado":"RECHAZADO","motivo":"Fondos insuficientes"}` | `RECHAZADO` (naranja) | «… pago RECHAZADO (Fondos insuficientes)» | `Fondos insuficientes` |
| `9999` | HTTP 500 `{"detail":"Error interno de la pasarela"}` | `ERROR` (rojo) | «… ERROR al procesar el pago (Pagos respondió HTTP 500)» | `Pagos respondió HTTP 500` |
| otra de 4 dígitos | HTTP 200 `RECHAZADO` | `RECHAZADO` | «… (Tarjeta no reconocida)» | `Tarjeta no reconocida` |
| formato inválido (`55`, letras) | HTTP 422 | no se crea el pedido | «No se pudo crear el pedido: HTTP 422» | — |
| Pagos caído o sin responder | sin respuesta / timeout | `ERROR` | «… ERROR … (Pagos no disponible: …)» | `Pagos no disponible: ConnectError` |

En los tres casos principales **Pedidos responde 201 y el pedido siempre se guarda**: lo que cambia es el estado del pago. Un rechazo no es un error técnico (Pagos respondió bien, con un «no»); un error 500 sí lo es.

## Ejecutar en local

Requisitos: Docker con Compose v2 y Python 3.12.

```bash
cd Src
docker compose up --build            # o con -d --wait para dejarlo en segundo plano
```

- Tienda: http://localhost:8080
- Documentación interactiva de Pedidos: http://localhost:8000/docs
- Documentación interactiva de Pagos: http://localhost:8001/docs

Cada arranque de `pedidos` borra y crea `data/pedidos.db` (`RESET_DB=true`), así no quedan datos de corridas anteriores.

### Pruebas

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r pedidos/requirements.txt -r pedidos/requirements-dev.txt -r pruebas/requirements.txt
playwright install chromium

pytest pedidos/tests            # 6 pruebas estrechas, no necesitan Docker
cd pruebas && pytest            # 10 pruebas amplias, necesitan los 3 contenedores arriba
```

Salida esperada: `6 passed` y `10 passed`.

## Dónde ver el reporte, las capturas y los videos

| Qué | Dónde (local, dentro de `pruebas/`) |
|---|---|
| Reporte HTML (abrir en el navegador) | `reporte/index.html` — cada prueba de la tienda trae incrustadas las capturas «formulario» y «resultado» |
| Capturas tomadas por las pruebas | `reporte/capturas/<prueba>-formulario.png` y `-resultado.png` |
| Captura final automática de Playwright | `test-results/<prueba>/test-finished-1.png` |
| Video de cada prueba de la tienda | `test-results/<prueba>/video.webm` |
| Traza de Playwright (solo si la prueba falla) | `test-results/<prueba>/trace.zip` → abrir con `playwright show-trace trace.zip` o en https://trace.playwright.dev |

## Subirlo a GitHub y correrlo en GitHub Actions

1. Cree un repositorio vacío en GitHub.
2. Suba **el contenido de `Src/` como raíz del repositorio** (el workflow debe quedar en `.github/workflows/` de la raíz):
   ```bash
   cd Src
   git init -b main
   git add .
   git commit -m "Taller de pruebas de integración"
   git remote add origin https://github.com/<usuario>/<repositorio>.git
   git push -u origin main
   ```
3. El `push` dispara el workflow «Pruebas de integracion». También se puede lanzar a mano en la pestaña **Actions → Pruebas de integracion → Run workflow**.
4. Lo que se espera ver en Actions:
   - Trabajo **estrechas**: instala Pedidos y corre `pedidos/tests` (6 pruebas).
   - Trabajo **amplias** (solo si el anterior pasó): crea una carpeta `data` vacía, levanta los 3 contenedores y espera a que estén sanos, instala Playwright, corre las 10 pruebas, guarda los logs y publica el artefacto.
5. Para descargar la evidencia: abra la ejecución → sección **Artifacts** al final → `reporte-playwright` (zip con `pruebas/reporte/`, `pruebas/test-results/` y `docker-logs.txt`). El artefacto se publica **siempre**, también cuando una prueba falla (`if: always()`); es justamente en el fallo cuando más sirve.

### Provocar un fallo a propósito (para el taller)

- Cambie en `pagos/app.py` el código 500 por 503 → falla solo `test_pagos_api.py::...[error-500]` (el contrato de Pagos cambió), pero las pruebas de Pedidos y de la tienda siguen pasando porque Pedidos trata cualquier 5xx como `ERROR`.
- Cambie en `pedidos/app.py` el estado `"ERROR"` por `"FALLIDO"` → fallan la estrecha y las amplias; el reporte muestra la diferencia y queda la traza.
- Cambie `PAGOS_URL` en `docker-compose.yml` a un puerto incorrecto → todos los pedidos quedan en `ERROR` y fallan los casos aprobado y rechazado

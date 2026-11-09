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
Integration-Testing/
├── docker-compose.yml               # levanta pagos, pedidos y frontend
├── .github/workflows/pruebas-integracion.yml
├── pagos/        app.py, Dockerfile, requirements.txt
├── pedidos/      app.py, Dockerfile, requirements*.txt
│   └── tests/    conftest.py, test_pedidos_estrecha.py   # estrecha: Pagos reemplazado por un doble
├── frontend/     Dockerfile, templates/default.conf.template, public/ (index.html, app.js, styles.css)
├── pruebas/      pytest.ini, conftest.py, requirements.txt
│   ├── test_pagos_api.py            # Pagos aislado (contrato)
│   ├── test_pedidos_pagos_real.py   # Pedidos + Pagos reales
│   ├── test_pedidos_api.py          # Pedidos + Pagos + SQLite
│   └── test_tienda_e2e.py           # Playwright: navegador + 3 contenedores
└── soluciones/   (solo en el repositorio del equipo; no se incluye en el .zip del taller)
    ├── README.md                            # cómo usarlas y fallos provocados
    ├── test_pedidos_estrecha_solucion.py    # CP-17 a CP-20
    ├── test_pedidos_pagos_real_solucion.py  # CP-21 a CP-24
    ├── test_pedidos_api_solucion.py         # CP-25 a CP-28
    └── test_tienda_e2e_solucion.py          # CP-29 a CP-32
```

## Resultados esperados

| Tarjeta | Respuesta de Pagos | `estado_pago` en Pedidos y SQLite | Mensaje en la tienda |
|---|---|---|---|
| `5500` | HTTP 200, `APROBADO` y código de autorización | `APROBADO` (verde) | «Pedido #N creado: pago APROBADO» |
| `0000` | HTTP 200, `RECHAZADO`, motivo «Fondos insuficientes» | `RECHAZADO` (naranja) | «… pago RECHAZADO (Fondos insuficientes)» |
| `9999` | HTTP 500, «Error interno de la pasarela» | `ERROR` (rojo) | «… ERROR al procesar el pago (Pagos respondió HTTP 500)» |
| otra de 4 dígitos (ej. `1234`) | HTTP 200, `RECHAZADO`, motivo «Tarjeta no reconocida» | `RECHAZADO` | «… pago RECHAZADO (Tarjeta no reconocida)» |
| formato inválido (`55`, costo 0) | no se llama a Pagos; Pedidos responde 422 | no se guarda | «No se pudo crear el pedido: HTTP 422» |
| Pagos caído o sin responder | sin respuesta o tiempo agotado | `ERROR` | «… ERROR … (Pagos no disponible: …)» |

Todo pedido **válido** se guarda y Pedidos responde 201: lo que cambia es el estado del pago. Un rechazo no es un error técnico (Pagos respondió bien, con un «no»); un 500 sí lo es.

## Casos de prueba

- **CP-01 a CP-16** vienen resueltos.
- **CP-17 a CP-32** son la práctica: 4 ejercicios al final de cada archivo (3 fáciles y 1 medio), cada uno con su enunciado en el docstring y un `pytest.skip` que se reemplaza por la prueba.

| Archivo | Resueltos | Práctica |
|---|---|---|
| `pedidos/tests/test_pedidos_estrecha.py` | CP-01 a CP-06 | CP-17 a CP-20 |
| `pruebas/test_pagos_api.py` | CP-07 a CP-10 | — |
| `pruebas/test_pedidos_pagos_real.py` | — | CP-21 a CP-24 |
| `pruebas/test_pedidos_api.py` | CP-11 a CP-13 | CP-25 a CP-28 |
| `pruebas/test_tienda_e2e.py` | CP-14 a CP-16 | CP-29 a CP-32 |

## Pasos del taller

Requisitos: Docker con Compose v2, Python 3.12, Git, un navegador y una cuenta de GitHub. Los comandos son para PowerShell (Windows); en Linux/Mac el entorno se activa con `source .venv/bin/activate`.

**1. Preparar el ambiente.** Descomprimir el .zip del taller y abrir una terminal en la carpeta `Integration-Testing`.

**2. Levantar el sistema y preparar Python.**
```powershell
docker compose up -d --build --wait     # los 3 contenedores deben quedar "healthy"
docker compose ps
python -m venv .venv
.\.venv\Scripts\Activate.ps1            # si PowerShell lo bloquea: Set-ExecutionPolicy -Scope Process Bypass
pip install -r pedidos/requirements.txt -r pedidos/requirements-dev.txt -r pruebas/requirements.txt
playwright install chromium
```

**3. Explorar manualmente.** Abrir http://localhost:8080 y crear un pedido con 5500, 0000, 9999 y 1234. Revisar http://localhost:8000/docs y http://localhost:8001/docs.

**4. Ejecutar las pruebas existentes.**
```powershell
pytest pedidos/tests     # 6 passed, 4 skipped
cd pruebas
pytest                   # 10 passed, 12 skipped
cd ..
```

**5. Revisar la evidencia.**
```powershell
start pruebas\reporte\index.html
start pruebas\reporte\capturas
start pruebas\test-results
```

| Qué | Dónde (dentro de `pruebas/`) |
|---|---|
| Reporte HTML | `reporte/index.html`, con las capturas «formulario» y «resultado» incrustadas |
| Capturas de las pruebas de interfaz | `reporte/capturas/` |
| Captura final y video de cada prueba con navegador | `test-results/<prueba>/test-finished-1.png` y `video.webm` |
| Traza (solo si la prueba falla) | `test-results/<prueba>/trace.zip` → `playwright show-trace trace.zip` o https://trace.playwright.dev |

**6. Verificar la base de datos.**
```powershell
python -c "import sqlite3; [print(r) for r in sqlite3.connect('data/pedidos.db').execute('select * from pedidos')]"
```
La base se borra y se crea vacía cada vez que arranca el contenedor de Pedidos.

**7. Resolver la práctica.** Resolver los ejercicios de cada archivo en este orden: `test_pedidos_estrecha.py`, `test_pedidos_pagos_real.py`, `test_pedidos_api.py` y `test_tienda_e2e.py`, ejecutando el archivo después de cada uno. Al terminar: `10 passed` en las estrechas y `22 passed` en las amplias, sin omitidas.

**8. Automatizar en GitHub Actions.** El contenido de `Integration-Testing` debe quedar como raíz del repositorio (GitHub solo lee `.github/workflows` de la raíz):
```powershell
git init -b main
git add .
git commit -m "Taller de pruebas de integración"
git remote add origin https://github.com/<usuario>/<repositorio>.git
git push -u origin main
```
En la pestaña **Actions** se ejecutan dos trabajos: **estrechas** (10 pruebas) y, si pasa, **amplias** (levanta los 3 contenedores y ejecuta 22 pruebas). Al terminar, descargar el artefacto `reporte-playwright` en la sección **Artifacts**: trae el reporte, las capturas, los videos y `docker-logs.txt`. Se publica siempre, también cuando una prueba falla. Opcionalmente, con la CLI de GitHub: `gh run watch` y `gh run download --name reporte-playwright`.

**9. Provocar fallos y analizarlos.** Aplicar los cambios uno a uno, reconstruir, ejecutar las pruebas y registrar qué falla y por qué. Restaurar con `git checkout -- <archivo>` antes del siguiente.

| Cambio | Defecto que simula | Comandos |
|---|---|---|
| En `pagos/app.py`, `status_code=500` → `503` | El proveedor cambia su contrato sin avisar | `docker compose up -d --build --wait` y `cd pruebas; pytest` |
| En `pedidos/app.py`, dentro de `cobrar()`, `"ERROR"` → `"FALLIDO"` (sin tocar el CHECK del esquema) | Pedidos y la base no coinciden en los estados válidos | `pytest pedidos/tests`, `docker compose up -d --build --wait` y `cd pruebas; pytest` |
| En `docker-compose.yml`, `PAGOS_URL: http://pagos:8002` | Error de configuración del entorno | `docker compose up -d --wait`, `pytest pedidos/tests` (siguen pasando) y `cd pruebas; pytest` |

**10. Comparar con las soluciones.** Las soluciones de referencia están en el repositorio del equipo: https://github.com/chris124v/Integration-Testing

Al terminar: `docker compose down`.

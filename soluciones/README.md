# Soluciones de referencia (solo instructor)

Esta carpeta **no se entrega** a los participantes: se elimina del .zip del taller.

Cada archivo es la versión completa del archivo de práctica, con los casos existentes y los ejercicios resueltos:

| Solución | Reemplaza a | Ejercicios |
|---|---|---|
| `test_pedidos_estrecha_solucion.py` | `pedidos/tests/test_pedidos_estrecha.py` | CP-17 a CP-20 |
| `test_pedidos_pagos_real_solucion.py` | `pruebas/test_pedidos_pagos_real.py` | CP-21 a CP-24 |
| `test_pedidos_api_solucion.py` | `pruebas/test_pedidos_api.py` | CP-25 a CP-28 |
| `test_tienda_e2e_solucion.py` | `pruebas/test_tienda_e2e.py` | CP-29 a CP-32 |

## Cómo ejecutarlas

Las pruebas necesitan las fixtures del `conftest.py` de su carpeta, así que se copian sobre el archivo de práctica (quitando el sufijo `_solucion`):

```powershell
cp soluciones/test_pedidos_estrecha_solucion.py pedidos/tests/test_pedidos_estrecha.py
cp soluciones/test_pedidos_pagos_real_solucion.py pruebas/test_pedidos_pagos_real.py
cp soluciones/test_pedidos_api_solucion.py pruebas/test_pedidos_api.py
cp soluciones/test_tienda_e2e_solucion.py pruebas/test_tienda_e2e.py

pytest pedidos/tests        # 10 passed
cd pruebas; pytest          # 22 passed
```

Para volver a la versión de práctica: `git checkout -- pedidos/tests pruebas`.

## Resultado de los fallos provocados con estas soluciones

| Fallo | Casos que fallan |
|---|---|
| 500 → 503 en `pagos/app.py` | CP-09, CP-23 y CP-25 |
| «FALLIDO» en lugar de «ERROR» en `cobrar()` | CP-03 a CP-05, CP-13, CP-16 a CP-18 y CP-22 a CP-25 |
| `PAGOS_URL` con puerto incorrecto | CP-11, CP-12, CP-14, CP-15, CP-21 a CP-25 y CP-29 a CP-32 |

Una solución distinta del participante puede detectar más o menos casos; por ejemplo, CP-24 resuelto comparando contra el código que devuelve Pagos no falla con el cambio a 503.

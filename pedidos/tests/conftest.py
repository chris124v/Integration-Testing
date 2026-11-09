# Agrega la carpeta pedidos/ al path de Python para que las pruebas puedan
# hacer "import app" y probar el servicio Pedidos directamente, sin Docker.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

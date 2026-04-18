"""
Pruebas API solicitudes (CU15 y seguridad básica).

Ejecutar (con .env y base de datos accesible):
  cd taller_backend
  pytest tests/test_solicitudes_cu15.py -v

Sin DB solo se valida comportamiento sin autenticación (no requiere tablas).
"""

from fastapi.testclient import TestClient


def test_aceptar_sin_token_rechaza():
    from app.main import app

    client = TestClient(app)
    r = client.patch("/api/solicitudes/1/aceptar", json={})
    assert r.status_code in (401, 403)


def test_disponibles_sin_token_rechaza():
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/solicitudes/disponibles")
    assert r.status_code in (401, 403)

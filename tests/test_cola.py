from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models import EntradaCola
from main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        db = SessionLocal()
        db.query(EntradaCola).delete()
        db.commit()
        db.close()
        yield test_client


def _nombre() -> str:
    return f"Test {uuid4().hex[:8]}"


def _crear(client: TestClient, nombre: str, personas: int = 2, local_id: int = 1) -> dict:
    response = client.post(
        "/cola",
        json={
            "id_local": local_id,
            "nombre_comensal": nombre,
            "telefono_comensal": "999111222",
            "cantidad_personas": personas,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _mesa_con_capacidad(client: TestClient, local_id: int, capacidad_minima: int) -> dict:
    response = client.get(f"/locales/{local_id}/mesas")
    assert response.status_code == 200
    mesa = next(item for item in response.json() if item["capacidad"] >= capacidad_minima)
    return mesa


def test_flujo_principal_de_cola(client: TestClient):
    primero = _crear(client, _nombre(), personas=4)
    segundo = _crear(client, _nombre(), personas=2)
    tercero = _crear(client, _nombre(), personas=3)

    assert primero["puesto"] == 1
    assert segundo["puesto"] == 2
    assert tercero["tiempo_estimado_minutos"] == 45

    cola = client.get("/cola", params={"local_id": 1})
    assert cola.status_code == 200
    ids = [item["id"] for item in cola.json()]
    assert primero["id"] in ids and segundo["id"] in ids and tercero["id"] in ids

    puesto = client.get(f"/cola/{segundo['id']}")
    assert puesto.status_code == 200
    assert puesto.json()["personas_adelante"] >= 1

    actualizado = client.patch(
        f"/cola/{segundo['id']}",
        json={"tiempo_estimado_minutos": 20, "es_frecuente": True},
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["tiempo_estimado_minutos"] == 20
    assert actualizado.json()["es_frecuente"] is True

    reordenado = client.put(f"/cola/{tercero['id']}/reordenar", json={"orden": 1})
    assert reordenado.status_code == 200
    assert reordenado.json()["puesto"] == 1

    llamado = client.patch(f"/cola/{tercero['id']}/llamar")
    assert llamado.status_code == 200
    assert llamado.json()["estado"] == "llamado"
    assert llamado.json()["fecha_hora_llamado"] is not None

    mesa = _mesa_con_capacidad(client, 1, 3)
    sentado = client.patch(f"/cola/{tercero['id']}/sentar", json={"id_mesa": mesa["id"]})
    assert sentado.status_code == 200
    assert sentado.json()["estado"] == "sentado"
    assert sentado.json()["id_mesa"] == mesa["id"]
    assert sentado.json()["puesto"] is None

    client.patch(f"/cola/{primero['id']}/cancelar")
    client.patch(f"/cola/{segundo['id']}/cancelar")


def test_no_permite_nombre_duplicado_en_cola_activa(client: TestClient):
    nombre = _nombre()
    entrada = _crear(client, nombre)
    duplicado = client.post(
        "/cola",
        json={
            "id_local": 1,
            "nombre_comensal": nombre.upper(),
            "telefono_comensal": "988777666",
            "cantidad_personas": 2,
        },
    )
    assert duplicado.status_code == 409
    client.patch(f"/cola/{entrada['id']}/cancelar")


def test_no_show_solo_despues_de_llamar(client: TestClient):
    entrada = _crear(client, _nombre())
    temprano = client.patch(f"/cola/{entrada['id']}/no-show")
    assert temprano.status_code == 409

    client.patch(f"/cola/{entrada['id']}/llamar")
    no_show = client.patch(f"/cola/{entrada['id']}/no-show")
    assert no_show.status_code == 200
    assert no_show.json()["estado"] == "no_show"


def test_sentar_rechaza_mesa_chica(client: TestClient):
    entrada = _crear(client, _nombre(), personas=8)
    client.patch(f"/cola/{entrada['id']}/llamar")
    mesa_chica = next(
        item for item in client.get("/locales/1/mesas").json() if item["capacidad"] < 8
    )

    respuesta = client.patch(
        f"/cola/{entrada['id']}/sentar",
        json={"id_mesa": mesa_chica["id"]},
    )
    assert respuesta.status_code == 400
    client.patch(f"/cola/{entrada['id']}/cancelar")


def test_obtener_local_por_id(client: TestClient):
    respuesta = client.get("/local/1")
    assert respuesta.status_code == 200
    body = respuesta.json()
    assert body["id"] == 1
    assert body["nombre"]

    inexistente = client.get("/local/999")
    assert inexistente.status_code == 404

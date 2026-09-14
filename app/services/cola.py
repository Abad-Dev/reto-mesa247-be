from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EntradaCola, EstadoEntradaCola, Local, Mesa
from app.schemas import (
    ActualizarEntradaRequest,
    CrearEntradaRequest,
    EntradaColaResponse,
    ReordenarEntradaRequest,
    SentarEntradaRequest,
)

ESTADOS_EN_COLA = (
    EstadoEntradaCola.ESPERANDO,
    EstadoEntradaCola.LLAMADO,
    EstadoEntradaCola.EN_CAMINO,
)
ESTADOS_PARA_SENTAR = (EstadoEntradaCola.LLAMADO, EstadoEntradaCola.EN_CAMINO)
MINUTOS_POR_PUESTO = 15


def _ahora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _nombre_normalizado(nombre: str) -> str:
    return " ".join(nombre.split()).casefold()


def obtener_local_o_404(db: Session, local_id: int) -> Local:
    local = db.get(Local, local_id)
    if local is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local no encontrado")
    return local


def obtener_entrada_o_404(db: Session, entrada_id: int) -> EntradaCola:
    entrada = db.get(EntradaCola, entrada_id)
    if entrada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada de cola no encontrada")
    return entrada


def entradas_activas(db: Session, id_local: int) -> list[EntradaCola]:
    return list(
        db.scalars(
            select(EntradaCola)
            .where(
                EntradaCola.id_local == id_local,
                EntradaCola.estado.in_(ESTADOS_EN_COLA),
            )
            .order_by(EntradaCola.orden.asc(), EntradaCola.id.asc())
        ).all()
    )


def calcular_puesto(entrada: EntradaCola, activas: list[EntradaCola]) -> int | None:
    if entrada.estado not in ESTADOS_EN_COLA:
        return None
    for indice, actual in enumerate(activas, start=1):
        if actual.id == entrada.id:
            return indice
    return None


def compactar_orden(db: Session, id_local: int) -> None:
    for indice, entrada in enumerate(entradas_activas(db, id_local), start=1):
        entrada.orden = indice


def to_response(entrada: EntradaCola, activas: list[EntradaCola] | None = None) -> EntradaColaResponse:
    puesto = calcular_puesto(entrada, activas or [])
    payload = EntradaColaResponse.model_validate(entrada)
    return payload.model_copy(
        update={
            "puesto": puesto,
            "personas_adelante": None if puesto is None else puesto - 1,
        }
    )


def crear_entrada(db: Session, data: CrearEntradaRequest) -> EntradaCola:
    obtener_local_o_404(db, data.id_local)
    nombre = _nombre_normalizado(data.nombre_comensal)
    activas = entradas_activas(db, data.id_local)

    if any(_nombre_normalizado(entrada.nombre_comensal) == nombre for entrada in activas):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay una entrada activa con ese nombre en la cola de este local",
        )

    puesto = len(activas) + 1
    entrada = EntradaCola(
        id_local=data.id_local,
        nombre_comensal=data.nombre_comensal,
        telefono_comensal=data.telefono_comensal,
        cantidad_personas=data.cantidad_personas,
        estado=EstadoEntradaCola.ESPERANDO,
        orden=puesto,
        es_frecuente=False,
        tiempo_estimado_minutos=puesto * MINUTOS_POR_PUESTO,
    )
    db.add(entrada)
    db.commit()
    db.refresh(entrada)
    return entrada


def listar_cola(db: Session, local_id: int) -> list[EntradaCola]:
    obtener_local_o_404(db, local_id)
    return entradas_activas(db, local_id)


def actualizar_entrada(db: Session, entrada_id: int, data: ActualizarEntradaRequest) -> EntradaCola:
    entrada = obtener_entrada_o_404(db, entrada_id)
    if entrada.estado not in ESTADOS_EN_COLA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede actualizar una entrada que sigue en la cola",
        )

    if data.tiempo_estimado_minutos is not None:
        entrada.tiempo_estimado_minutos = data.tiempo_estimado_minutos
    if data.es_frecuente is not None:
        entrada.es_frecuente = data.es_frecuente

    db.commit()
    db.refresh(entrada)
    return entrada


def reordenar_entrada(db: Session, entrada_id: int, data: ReordenarEntradaRequest) -> EntradaCola:
    entrada = obtener_entrada_o_404(db, entrada_id)
    if entrada.estado not in ESTADOS_EN_COLA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede reordenar una entrada que sigue en la cola",
        )

    activas = [item for item in entradas_activas(db, entrada.id_local) if item.id != entrada.id]
    posicion = min(data.orden, len(activas) + 1)
    activas.insert(posicion - 1, entrada)

    for indice, item in enumerate(activas, start=1):
        item.orden = indice

    db.commit()
    db.refresh(entrada)
    return entrada


def llamar_entrada(db: Session, entrada_id: int) -> EntradaCola:
    entrada = obtener_entrada_o_404(db, entrada_id)
    if entrada.estado != EstadoEntradaCola.ESPERANDO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede llamar a un comensal que está esperando",
        )

    entrada.estado = EstadoEntradaCola.LLAMADO
    entrada.fecha_hora_llamado = _ahora()
    db.commit()
    db.refresh(entrada)
    return entrada


def marcar_en_camino(db: Session, entrada_id: int) -> EntradaCola:
    entrada = obtener_entrada_o_404(db, entrada_id)
    if entrada.estado != EstadoEntradaCola.LLAMADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo un comensal llamado puede indicar que va en camino",
        )

    entrada.estado = EstadoEntradaCola.EN_CAMINO
    db.commit()
    db.refresh(entrada)
    return entrada


def sentar_entrada(db: Session, entrada_id: int, data: SentarEntradaRequest) -> EntradaCola:
    entrada = obtener_entrada_o_404(db, entrada_id)
    if entrada.estado not in ESTADOS_PARA_SENTAR:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Primero hay que llamar al comensal antes de sentarlo",
        )

    mesa = db.get(Mesa, data.id_mesa)
    if mesa is None or mesa.id_local != entrada.id_local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no encontrada en este local")
    if mesa.capacidad < entrada.cantidad_personas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La mesa no tiene capacidad suficiente para este grupo",
        )

    entrada.estado = EstadoEntradaCola.SENTADO
    entrada.id_mesa = mesa.id
    compactar_orden(db, entrada.id_local)
    db.commit()
    db.refresh(entrada)
    return entrada


def cancelar_entrada(db: Session, entrada_id: int) -> EntradaCola:
    entrada = obtener_entrada_o_404(db, entrada_id)
    if entrada.estado not in ESTADOS_EN_COLA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede cancelar una entrada que sigue en la cola",
        )

    entrada.estado = EstadoEntradaCola.CANCELADO
    compactar_orden(db, entrada.id_local)
    db.commit()
    db.refresh(entrada)
    return entrada


def marcar_no_show(db: Session, entrada_id: int) -> EntradaCola:
    entrada = obtener_entrada_o_404(db, entrada_id)
    if entrada.estado not in ESTADOS_PARA_SENTAR:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede marcar no-show a un comensal que ya fue llamado",
        )

    entrada.estado = EstadoEntradaCola.NO_SHOW
    compactar_orden(db, entrada.id_local)
    db.commit()
    db.refresh(entrada)
    return entrada

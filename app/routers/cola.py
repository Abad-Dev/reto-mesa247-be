from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ActualizarEntradaRequest,
    CrearEntradaRequest,
    EntradaColaResponse,
    ReordenarEntradaRequest,
    SentarEntradaRequest,
)
from app.services import cola as cola_service

router = APIRouter(tags=["cola"])


@router.post("/cola", response_model=EntradaColaResponse, status_code=status.HTTP_201_CREATED)
def crear_entrada(payload: CrearEntradaRequest, db: Session = Depends(get_db)):
    entrada = cola_service.crear_entrada(db, payload)
    activas = cola_service.entradas_activas(db, entrada.id_local)
    return cola_service.to_response(entrada, activas)


@router.get("/cola", response_model=list[EntradaColaResponse])
def listar_cola(local_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    activas = cola_service.listar_cola(db, local_id)
    return [cola_service.to_response(entrada, activas) for entrada in activas]


@router.get("/cola/{entrada_id}", response_model=EntradaColaResponse)
def obtener_entrada(entrada_id: int, db: Session = Depends(get_db)):
    entrada = cola_service.obtener_entrada_o_404(db, entrada_id)
    activas = cola_service.entradas_activas(db, entrada.id_local)
    return cola_service.to_response(entrada, activas)


@router.patch("/cola/{entrada_id}", response_model=EntradaColaResponse)
def actualizar_entrada(
    entrada_id: int,
    payload: ActualizarEntradaRequest,
    db: Session = Depends(get_db),
):
    entrada = cola_service.actualizar_entrada(db, entrada_id, payload)
    activas = cola_service.entradas_activas(db, entrada.id_local)
    return cola_service.to_response(entrada, activas)


@router.put("/cola/{entrada_id}/reordenar", response_model=EntradaColaResponse)
def reordenar_entrada(
    entrada_id: int,
    payload: ReordenarEntradaRequest,
    db: Session = Depends(get_db),
):
    entrada = cola_service.reordenar_entrada(db, entrada_id, payload)
    activas = cola_service.entradas_activas(db, entrada.id_local)
    return cola_service.to_response(entrada, activas)


@router.patch("/cola/{entrada_id}/llamar", response_model=EntradaColaResponse)
def llamar_entrada(entrada_id: int, db: Session = Depends(get_db)):
    entrada = cola_service.llamar_entrada(db, entrada_id)
    activas = cola_service.entradas_activas(db, entrada.id_local)
    return cola_service.to_response(entrada, activas)


@router.patch("/cola/{entrada_id}/sentar", response_model=EntradaColaResponse)
def sentar_entrada(
    entrada_id: int,
    payload: SentarEntradaRequest,
    db: Session = Depends(get_db),
):
    entrada = cola_service.sentar_entrada(db, entrada_id, payload)
    return cola_service.to_response(entrada, [])


@router.patch("/cola/{entrada_id}/cancelar", response_model=EntradaColaResponse)
def cancelar_entrada(entrada_id: int, db: Session = Depends(get_db)):
    entrada = cola_service.cancelar_entrada(db, entrada_id)
    return cola_service.to_response(entrada, [])


@router.patch("/cola/{entrada_id}/no-show", response_model=EntradaColaResponse)
def marcar_no_show(entrada_id: int, db: Session = Depends(get_db)):
    entrada = cola_service.marcar_no_show(db, entrada_id)
    return cola_service.to_response(entrada, [])

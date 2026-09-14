from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Local, Mesa
from app.schemas import LocalResponse, MesaResponse
from app.services.cola import obtener_local_o_404

router = APIRouter(tags=["locales"])


@router.get("/locales", response_model=list[LocalResponse])
def listar_locales(db: Session = Depends(get_db)):
    return list(db.scalars(select(Local).order_by(Local.id.asc())).all())


@router.get("/local/{local_id}", response_model=LocalResponse)
def obtener_local(local_id: int, db: Session = Depends(get_db)):
    return obtener_local_o_404(db, local_id)


@router.get("/locales/{local_id}/mesas", response_model=list[MesaResponse])
def listar_mesas(local_id: int, db: Session = Depends(get_db)):
    obtener_local_o_404(db, local_id)
    return list(
        db.scalars(select(Mesa).where(Mesa.id_local == local_id).order_by(Mesa.id.asc())).all()
    )

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import EstadoEntradaCola


class CrearEntradaRequest(BaseModel):
    id_local: int
    nombre_comensal: str = Field(min_length=1, max_length=120)
    telefono_comensal: str = Field(min_length=6, max_length=30)
    cantidad_personas: int = Field(ge=1, le=20)

    @field_validator("nombre_comensal", "telefono_comensal")
    @classmethod
    def strip_texto(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("El campo no puede estar vacío")
        return cleaned


class ActualizarEntradaRequest(BaseModel):
    tiempo_estimado_minutos: int | None = Field(default=None, ge=0)
    es_frecuente: bool | None = None

    @model_validator(mode="after")
    def al_menos_un_campo(self) -> "ActualizarEntradaRequest":
        if self.tiempo_estimado_minutos is None and self.es_frecuente is None:
            raise ValueError("Debe enviar tiempo_estimado_minutos o es_frecuente")
        return self


class ReordenarEntradaRequest(BaseModel):
    orden: int = Field(ge=1, description="Nueva posición en la cola (1 = primero)")


class SentarEntradaRequest(BaseModel):
    id_mesa: int


class EntradaColaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_local: int
    nombre_comensal: str
    telefono_comensal: str
    cantidad_personas: int
    estado: EstadoEntradaCola
    orden: int
    es_frecuente: bool
    id_mesa: int | None
    fecha_hora_union: datetime
    fecha_hora_llamado: datetime | None
    tiempo_estimado_minutos: int | None
    puesto: int | None = None
    personas_adelante: int | None = None


class LocalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class MesaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_local: int
    capacidad: int

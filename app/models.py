import enum
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EstadoEntradaCola(str, enum.Enum):
    ESPERANDO = "esperando"
    LLAMADO = "llamado"
    EN_CAMINO = "en_camino"
    SENTADO = "sentado"
    NO_SHOW = "no_show"
    CANCELADO = "cancelado"


class Local(Base):
    __tablename__ = "local"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)

    mesas: Mapped[list["Mesa"]] = relationship(back_populates="local")
    entradas_cola: Mapped[list["EntradaCola"]] = relationship(back_populates="local")


class Mesa(Base):
    __tablename__ = "mesa"
    __table_args__ = (
        CheckConstraint("capacidad > 0", name="ck_mesa_capacidad_positiva"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_local: Mapped[int] = mapped_column(ForeignKey("local.id", ondelete="RESTRICT"), nullable=False)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False)

    local: Mapped["Local"] = relationship(back_populates="mesas")
    entradas_cola: Mapped[list["EntradaCola"]] = relationship(back_populates="mesa")


class EntradaCola(Base):
    __tablename__ = "entrada_cola"
    __table_args__ = (
        CheckConstraint("cantidad_personas > 0", name="ck_entrada_cola_cantidad_positiva"),
        CheckConstraint(
            "tiempo_estimado_minutos IS NULL OR tiempo_estimado_minutos >= 0",
            name="ck_entrada_cola_tiempo_estimado",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_local: Mapped[int] = mapped_column(ForeignKey("local.id", ondelete="RESTRICT"), nullable=False)
    nombre_comensal: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono_comensal: Mapped[str] = mapped_column(String(30), nullable=False)
    cantidad_personas: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoEntradaCola] = mapped_column(
        Enum(EstadoEntradaCola, values_callable=lambda enum_cls: [item.value for item in enum_cls], native_enum=False),
        nullable=False,
        default=EstadoEntradaCola.ESPERANDO,
    )
    orden: Mapped[int] = mapped_column("orden", Integer, nullable=False)
    es_frecuente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    id_mesa: Mapped[int | None] = mapped_column(ForeignKey("mesa.id", ondelete="SET NULL"), nullable=True)
    fecha_hora_union: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    fecha_hora_llamado: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tiempo_estimado_minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)

    local: Mapped["Local"] = relationship(back_populates="entradas_cola")
    mesa: Mapped["Mesa | None"] = relationship(back_populates="entradas_cola")

import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Cafe
from app.regras import DescontoInvalido, preco_com_desconto

app = FastAPI(title="Café com Deploy")

DB = Annotated[Session, Depends(get_db)]


def cardapio_com_origem() -> bool:
    # Feature flag: ligada em staging, desligada em produção até a validação.
    return os.getenv("FEATURE_CARDAPIO_ORIGEM", "false").lower() in {"1", "true", "on"}


class CafeEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    preco: float = Field(gt=0, lt=10000)
    origem: str | None = Field(default=None, min_length=1, max_length=60)


class CafeSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco: float
    origem: str | None = None


class PrecoSaida(BaseModel):
    id: int
    nome: str
    preco: float
    desconto: float
    preco_final: float


def buscar_cafe(db: Session, cafe_id: int) -> Cafe:
    cafe = db.get(Cafe, cafe_id)
    if cafe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Café não encontrado")
    return cafe


def para_saida(cafe: Cafe) -> CafeSaida:
    saida = CafeSaida.model_validate(cafe)
    if not cardapio_com_origem():
        saida.origem = None
    return saida


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": os.getenv("APP_VERSION", "dev")}


@app.get("/cafes", response_model=list[CafeSaida], response_model_exclude_none=True)
def listar_cafes(db: DB):
    return [para_saida(cafe) for cafe in db.scalars(select(Cafe).order_by(Cafe.id))]


@app.post(
    "/cafes",
    response_model=CafeSaida,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
def criar_cafe(dados: CafeEntrada, db: DB):
    cafe = Cafe(**dados.model_dump(exclude_none=True))
    db.add(cafe)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um café com esse nome") from None
    db.refresh(cafe)
    return para_saida(cafe)


@app.get("/cafes/{cafe_id}", response_model=CafeSaida, response_model_exclude_none=True)
def obter_cafe(cafe_id: int, db: DB):
    return para_saida(buscar_cafe(db, cafe_id))


@app.get("/cafes/{cafe_id}/preco", response_model=PrecoSaida)
def obter_preco(cafe_id: int, db: DB, desconto: Annotated[float, Query()] = 0):
    cafe = buscar_cafe(db, cafe_id)
    try:
        final = preco_com_desconto(cafe.preco, desconto)
    except DescontoInvalido as erro:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erro)) from None
    return PrecoSaida(
        id=cafe.id, nome=cafe.nome, preco=cafe.preco, desconto=desconto, preco_final=final
    )

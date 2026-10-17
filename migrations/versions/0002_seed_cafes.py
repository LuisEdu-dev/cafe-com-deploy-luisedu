"""seed do cardapio inicial

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

cafes = sa.table(
    "cafes",
    sa.column("nome", sa.String),
    sa.column("preco", sa.Numeric),
)

CARDAPIO = [
    {"nome": "Espresso Esplanada", "preco": 7.50},
    {"nome": "Coado do Cerrado", "preco": 9.00},
    {"nome": "Cappuccino Catedral", "preco": 12.90},
    {"nome": "Latte Lago Paranoá", "preco": 13.50},
    {"nome": "Mocha Memorial JK", "preco": 14.90},
    {"nome": "Cortado Congresso", "preco": 8.90},
    {"nome": "Macchiato Torre de TV", "preco": 10.50},
]


def upgrade() -> None:
    op.bulk_insert(cafes, CARDAPIO)


def downgrade() -> None:
    nomes = [cafe["nome"] for cafe in CARDAPIO]
    op.execute(cafes.delete().where(cafes.c.nome.in_(nomes)))

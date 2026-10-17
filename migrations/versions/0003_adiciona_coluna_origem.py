"""adiciona coluna origem

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-17 02:58:41.200225

Fase EXPAND do padrão expandir/contrair: a coluna nasce com server_default,
então imagens antigas (que não conhecem "origem") continuam inserindo e lendo
cafés normalmente. Nenhuma coluna é removida ou renomeada aqui.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ORIGEM_PADRAO = "Cerrado Mineiro"


def upgrade() -> None:
    with op.batch_alter_table("cafes") as batch:
        batch.add_column(
            sa.Column("origem", sa.String(60), nullable=False, server_default=ORIGEM_PADRAO)
        )


def downgrade() -> None:
    with op.batch_alter_table("cafes") as batch:
        batch.drop_column("origem")

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.models import Cafe


def revisao_atual(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()


def test_migrations_aplicam_do_zero(engine, alembic_config):
    head = ScriptDirectory.from_config(alembic_config).get_current_head()

    command.downgrade(alembic_config, "base")
    assert "cafes" not in inspect(engine).get_table_names()

    command.upgrade(alembic_config, "head")

    assert revisao_atual(engine) == head
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM cafes")).scalar() >= 5


def test_seed_pode_ser_revertido(engine, alembic_config):
    command.downgrade(alembic_config, "0001")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM cafes")).scalar() == 0

    command.upgrade(alembic_config, "head")


def test_nome_e_unico_no_banco(db_session):
    db_session.add(Cafe(nome="Espresso Esplanada", preco=1))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_preco_volta_como_float(db_session):
    cafe = db_session.scalars(select(Cafe).order_by(Cafe.id)).first()

    assert isinstance(cafe.preco, float)


def test_migration_3_preserva_compatibilidade_com_codigo_antigo(engine):
    # Código anterior à Migration 3 insere sem conhecer a coluna "origem".
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO cafes (nome, preco) VALUES ('Café Legado', 5)"))
        origem = conn.execute(text("SELECT origem FROM cafes WHERE nome = 'Café Legado'")).scalar()
        conn.execute(text("DELETE FROM cafes WHERE nome = 'Café Legado'"))

    assert origem == "Cerrado Mineiro"


def test_migration_3_pode_ser_revertida(engine, alembic_config):
    command.downgrade(alembic_config, "0002")
    colunas = {coluna["name"] for coluna in inspect(engine).get_columns("cafes")}
    command.upgrade(alembic_config, "head")

    assert "origem" not in colunas
    assert "origem" in {coluna["name"] for coluna in inspect(engine).get_columns("cafes")}

from alembic import command
from sqlalchemy import text

from scripts.start import migrar


def test_start_migra_banco_desatualizado(engine, alembic_config):
    command.downgrade(alembic_config, "0001")

    assert migrar(alembic_config) is True

    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"


def test_start_nao_migra_banco_a_frente_da_imagem(engine, alembic_config):
    # Simula rollback: o banco foi migrado por uma imagem mais nova.
    with engine.begin() as conn:
        conn.execute(text("UPDATE alembic_version SET version_num = '9999'"))
    try:
        assert migrar(alembic_config) is False
        with engine.connect() as conn:
            assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "9999"
    finally:
        with engine.begin() as conn:
            conn.execute(text("UPDATE alembic_version SET version_num = '0002'"))

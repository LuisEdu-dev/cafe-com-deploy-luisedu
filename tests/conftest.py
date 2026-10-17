import os
import tempfile
from pathlib import Path

# Os testes NUNCA usam o DATABASE_URL do ambiente (que pode ser produção):
# usam TEST_DATABASE_URL (Postgres no CI) ou um SQLite temporário.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or (
    "sqlite:///" + (Path(tempfile.mkdtemp()) / "teste.db").as_posix()
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, delete, make_url, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Cafe  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def alembic_config():
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session")
def engine(alembic_config):
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    Sessao = sessionmaker(bind=engine, expire_on_commit=False)
    with Sessao() as session:
        ids_iniciais = set(session.scalars(select(Cafe.id)))
        yield session
        session.rollback()
        # Remove o que o teste criou, preservando o seed das migrations.
        session.execute(delete(Cafe).where(Cafe.id.not_in(ids_iniciais)))
        session.commit()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def pytest_report_header():
    url = make_url(TEST_DATABASE_URL)
    return f"banco de teste: {url.render_as_string(hide_password=True)}"

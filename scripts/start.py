"""Entrypoint do container: aplica migrations com segurança e sobe a API.

Se o banco estiver numa revisão que esta imagem não conhece (ex.: rollback para
uma imagem anterior à Migration 3), NÃO migra: só avisa e sobe a API. Isso funciona
porque as migrations seguem expand/contract — o schema novo continua compatível
com o código antigo.
"""

import logging
import os
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
from sqlalchemy import create_engine

RAIZ = Path(__file__).resolve().parent.parent

log = logging.getLogger("start")


def revisoes_do_banco(url: str) -> set[str]:
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return set(MigrationContext.configure(conn).get_current_heads())
    finally:
        engine.dispose()


def migrar(config: Config) -> bool:
    """Aplica `upgrade head`, exceto se o banco estiver à frente desta imagem."""
    url = config.get_main_option("sqlalchemy.url") or os.environ["DATABASE_URL"]
    scripts = ScriptDirectory.from_config(config)

    for revisao in revisoes_do_banco(url):
        try:
            scripts.get_revision(revisao)
        except CommandError:
            log.warning(
                "Banco na revisão %s, desconhecida por esta imagem (head=%s). "
                "Provável rollback: migrations NÃO serão aplicadas.",
                revisao,
                scripts.get_current_head(),
            )
            return False

    command.upgrade(config, "head")
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    config = Config(str(RAIZ / "alembic.ini"))
    config.attributes["configure_logger"] = False
    migrar(config)

    porta = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=porta, proxy_headers=True)


if __name__ == "__main__":
    main()

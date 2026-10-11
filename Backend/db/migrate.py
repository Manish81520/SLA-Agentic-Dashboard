"""Alembic migration entrypoint."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_to_head() -> None:
    """Upgrade the configured database to the current schema revision."""
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "Backend" / "db" / "migrations"))
    command.upgrade(config, "head")

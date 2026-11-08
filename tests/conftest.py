"""Shared fixtures. Tests must NEVER touch the real database or uploads folder."""
import pytest

from utils import auth


@pytest.fixture(autouse=True)
def _clean_admin_env(monkeypatch):
    """Start every test with no admin password in the environment."""
    monkeypatch.delenv(auth.ENV_VAR, raising=False)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Point the database layer at a throw-away directory."""
    from database import db

    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "UPLOAD_DIR", tmp_path / "uploads")
    db.init_db()
    return tmp_path

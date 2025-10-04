from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.db import session as session_module


def test_get_db_yields_session_and_closes(monkeypatch):
    created: list[SimpleNamespace] = []

    def fake_session_local():
        handle = SimpleNamespace(closed=False)

        def close() -> None:
            handle.closed = True

        handle.close = close
        created.append(handle)
        return handle

    monkeypatch.setattr(session_module, "SessionLocal", fake_session_local)

    generator = session_module.get_db()
    db = next(generator)
    assert db is created[0]

    generator.close()
    assert created[0].closed is True

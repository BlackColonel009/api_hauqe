import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
import pytest

from app.tasks import process_notification_queue as queue


def finish_without_io(coro):
    # Disabled paths must finish before any actual async I/O is scheduled.
    with pytest.raises(StopIteration):
        coro.send(None)


def test_disabled_direct_smtp_is_blocked():
    with patch.object(queue.settings, 'hauqe_smtp_enabled', False), \
         patch.object(queue.smtplib, 'SMTP') as smtp:
        with pytest.raises(RuntimeError, match='désactivé'):
            queue.send_smtp(recipient='test@example.invalid', subject='Test', body='Test')
        smtp.assert_not_called()


def test_disabled_smtp_does_not_open_database_or_send():
    with patch.object(queue.settings, 'hauqe_smtp_enabled', False), \
         patch.object(queue, 'AsyncSessionLocal') as db, \
         patch.object(queue, 'send_smtp') as send:
        finish_without_io(queue.run())
        db.assert_not_called()
        send.assert_not_called()


def test_disabled_embedded_worker_is_not_started():
    tree = ast.parse(Path('app/main.py').read_text(encoding='utf-8'))
    lifespan = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'lifespan')
    lifespan.args.args[0].annotation = None
    serve = AsyncMock()
    stop = AsyncMock()
    namespace = dict(asynccontextmanager=asynccontextmanager, asyncio=asyncio,
                     settings=SimpleNamespace(background_services_enabled=False),
                     serve=serve, stop=stop)
    exec(compile(ast.Module(body=[lifespan], type_ignores=[]), '<lifespan-test>', 'exec'), namespace)

    async def check():
        async with namespace['lifespan'](None):
            pass

    finish_without_io(check())
    serve.assert_not_called()
    stop.assert_awaited_once_with(None)

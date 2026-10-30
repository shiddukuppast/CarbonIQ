import asyncio
from typing import AsyncGenerator, Dict
import mongomock
import pytest
from httpx import ASGITransport, AsyncClient

from app.db.mongodb import reset_test_database, set_test_database
from app.main import app


class AsyncMockCursor:
    def __init__(self, sync_cursor):
        self._cursor = sync_cursor

    def sort(self, *args, **kwargs):
        self._cursor.sort(*args, **kwargs)
        return self

    def skip(self, n):
        self._cursor.skip(n)
        return self

    def limit(self, n):
        self._cursor.limit(n)
        return self

    def __aiter__(self):
        self._iter = iter(self._cursor)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class AsyncMockCollection:
    def __init__(self, sync_coll):
        self._coll = sync_coll

    async def insert_one(self, doc):
        return self._coll.insert_one(doc)

    async def find_one(self, *args, **kwargs):
        return self._coll.find_one(*args, **kwargs)

    def find(self, *args, **kwargs):
        return AsyncMockCursor(self._coll.find(*args, **kwargs))

    async def update_one(self, *args, **kwargs):
        return self._coll.update_one(*args, **kwargs)

    async def delete_one(self, *args, **kwargs):
        return self._coll.delete_one(*args, **kwargs)

    async def count_documents(self, *args, **kwargs):
        return self._coll.count_documents(*args, **kwargs)

    async def create_index(self, *args, **kwargs):
        return None


class AsyncMockDB:
    def __init__(self):
        self._client = mongomock.MongoClient()
        self._db = self._client.test_carboniq_db

    def __getattr__(self, name):
        return AsyncMockCollection(self._db[name])


@pytest.fixture(autouse=True)
def setup_test_db():
    """Sets a clean, isolated in-memory test database for every test function."""
    mock_db = AsyncMockDB()
    set_test_database(mock_db)
    yield mock_db
    reset_test_database()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous HTTP test client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def auth_header_helper():
    """Helper factory for creating Bearer token authorization headers."""
    def _make(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    return _make

import os
from surrealdb import Surreal

# Inisialisasi SurrealDB client
DB = Surreal()

def connect():
    url = os.getenv("SURREALDB_URL", "ws://localhost:8000")
    namespace = os.getenv("SURREALDB_NAMESPACE", "opennotebook")
    database = os.getenv("SURREALDB_DATABASE", "main")
    username = os.getenv("SURREALDB_USERNAME", "root")
    password = os.getenv("SURREALDB_PASSWORD", "root")
    DB.connect(url)
    DB.signin({"user": username, "pass": password})
    DB.use(namespace, database)

def repo_query(query: str):
    connect()
    return DB.query(query)

def repo_create(table: str, data: dict):
    connect()
    return DB.create(table, data)

def repo_update(id: str, data: dict):
    connect()
    return DB.update(id, data)

def repo_delete(id: str):
    connect()
    return DB.delete(id)

def repo_relate(source: str, relationship: str, target: str, data: dict = {}):
    connect()
    return DB.relate(source, relationship, target, data)

def repo_upsert(id: str, data: dict):
    connect()
    return DB.upsert(id, data)

def test_connection():
    try:
        connect()
        DB.query("INFO FOR DB")
        return True
    except Exception:
        return False
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from loguru import logger
from sblpy.connection import SurrealSyncConnection


@contextmanager
def db_connection():
    connection = SurrealSyncConnection(
        host=os.environ["SURREAL_ADDRESS"],
        port=int(os.environ["SURREAL_PORT"]),
        user=os.environ["SURREAL_USER"],
        password=os.environ["SURREAL_PASS"],
        namespace=os.environ["SURREAL_NAMESPACE"],
        database=os.environ["SURREAL_DATABASE"],
        max_size=2.2**20,
        encrypted=False,  # Set to True if using SSL
    )
    try:
        yield connection
    finally:
        connection.socket.close()


def repo_query(query_str: str, vars: Optional[Dict[str, Any]] = None):
    with db_connection() as connection:
        try:
            result = connection.query(query_str, vars)
            return result
        except Exception as e:
            logger.critical(f"Query: {query_str}")
            logger.exception(e)
            raise


def repo_create(table: str, data: Dict[str, Any]):
    query = f"CREATE {table} CONTENT {data};"
    return repo_query(query)


def repo_upsert(table: str, data: Dict[str, Any]):
    query = f"UPSERT {table} CONTENT {data};"
    return repo_query(query)


def repo_update(id: str, data: Dict[str, Any]):
    query = "UPDATE $id CONTENT $data;"
    vars = {"id": id, "data": data}
    return repo_query(query, vars)


def repo_delete(id: str):
    query = "DELETE $id;"
    vars = {"id": id}
    return repo_query(query, vars)


def repo_relate(source: str, relationship: str, target: str, data: Optional[Dict] = {}):
    query = f"RELATE {source}->{relationship}->{target} CONTENT $content;"
    result = repo_query(query, {"content": data})
    return result

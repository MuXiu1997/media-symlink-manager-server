import os
from functools import lru_cache

from media_symlink_manager_server.db import db
from media_symlink_manager_server.tmdb_client.client import TmdbClient

DEFAULT_DB_PATH = "/data/media_symlink_manager_server.db"


@lru_cache
def tmdb_client_from_env() -> TmdbClient:
    api_key = os.getenv("TMDB_API_KEY")
    db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
    if not api_key:
        raise ValueError("TMDB_API_KEY is not set")
    return TmdbClient(api_key, cache_db_path=db_path)


@lru_cache
def setup_db_from_env() -> None:
    db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
    db.bind(provider="sqlite", filename=db_path, create_db=True)
    db.generate_mapping(create_tables=True)

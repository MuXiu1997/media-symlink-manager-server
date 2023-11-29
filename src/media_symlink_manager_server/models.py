from datetime import datetime

from pony.orm import Required, Json, PrimaryKey  # type: ignore[import-untyped]

from media_symlink_manager_server.db import db


class TvModel(db.Entity):  # type: ignore[misc]
    _table_ = "tv"
    tmdb_id = PrimaryKey(int)
    name = Required(str)
    year = Required(int)
    tmdb_tv = Required(Json, column="tmdb_tv_json")
    tmdb_seasons = Required(Json, column="tmdb_seasons_json")
    filepath_mapping = Required(Json, column="filepath_mapping_json")
    created_at = Required(datetime)

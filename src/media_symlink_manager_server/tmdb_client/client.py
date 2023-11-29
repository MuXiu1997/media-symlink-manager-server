from typing import Optional

from requests_cache import CachedSession

from .requests import RequestSearchTv, RequestGetTvDetails, RequestGetTvSeasonDetails


class TmdbClient:
    BASE_URL = "https://api.themoviedb.org/3"
    headers = {"accept": "application/json"}

    def __init__(self, api_key: str, language: str = "zh-CN", cache_db_path: Optional[str] = None):
        self.api_key = api_key
        self.language = language

        self.search_tv = RequestSearchTv(tmdb_client=self)
        self.get_tv_details = RequestGetTvDetails(tmdb_client=self)
        self.get_tv_season_details = RequestGetTvSeasonDetails(tmdb_client=self)
        if cache_db_path:
            self.session = CachedSession(cache_db_path, backend="sqlite")
        else:
            self.session = CachedSession(backend="memory")

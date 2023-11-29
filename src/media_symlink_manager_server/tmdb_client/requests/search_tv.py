from typing import List, Optional, TYPE_CHECKING

from pydantic import ConfigDict
from typing_extensions import TypedDict

from ..utils import bool_str, first_not_none

if TYPE_CHECKING:
    from ..client import TmdbClient


class RequestSearchTv:
    class Response(TypedDict):
        __pydantic_config__ = ConfigDict(extra="allow")  # type: ignore[misc]

        page: int
        results: List["RequestSearchTv.FieldResultsItem"]
        total_pages: int
        total_results: int

    class FieldResultsItem(TypedDict):
        __pydantic_config__ = ConfigDict(extra="allow")  # type: ignore[misc]

        id: int
        name: str
        overview: str
        first_air_date: str
        poster_path: Optional[str]

    def __init__(self, tmdb_client: "TmdbClient"):
        self.tmdb_client = tmdb_client

    def __call__(
        self,
        query: str,
        first_air_date_year: Optional[str] = None,
        include_adult: bool = False,
        language: Optional[str] = None,
        page: int = 1,
        year: Optional[str] = None,
    ) -> "RequestSearchTv.Response":
        response: "RequestSearchTv.Response" = self.tmdb_client.session.request(
            method="GET",
            url=f"{self.tmdb_client.BASE_URL}/search/tv",
            headers=self.tmdb_client.headers,
            params={
                "api_key": self.tmdb_client.api_key,
                "query": query,
                "first_air_date_year": first_air_date_year,
                "include_adult": bool_str(include_adult),
                "language": first_not_none(language, self.tmdb_client.language),
                "page": page,
                "year": year,
            },
        ).json()
        return response

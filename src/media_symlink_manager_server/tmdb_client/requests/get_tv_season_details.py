from typing import List, TYPE_CHECKING, Optional

from pydantic import ConfigDict
from typing_extensions import TypedDict

from ..utils import first_not_none

if TYPE_CHECKING:
    from ..client import TmdbClient


class RequestGetTvSeasonDetails:
    class Response(TypedDict):
        __pydantic_config__ = ConfigDict(extra="allow")  # type: ignore[misc]

        name: str
        season_number: int
        episodes: List["RequestGetTvSeasonDetails.FieldEpisodesItem"]

    class FieldEpisodesItem(TypedDict):
        __pydantic_config__ = ConfigDict(extra="allow")  # type: ignore[misc]

        name: str
        season_number: int
        episode_number: int

    def __init__(self, tmdb_client: "TmdbClient"):
        self.tmdb_client = tmdb_client

    def __call__(
        self,
        series_id: int,
        season_number: int,
        append_to_response: Optional[str] = None,
        language: Optional[str] = None,
    ) -> "RequestGetTvSeasonDetails.Response":
        response: "RequestGetTvSeasonDetails.Response" = self.tmdb_client.session.request(
            method="GET",
            url=f"{self.tmdb_client.BASE_URL}/tv/{series_id}/season/{season_number}",
            headers=self.tmdb_client.headers,
            params={
                "api_key": self.tmdb_client.api_key,
                "append_to_response": append_to_response,
                "language": first_not_none(language, self.tmdb_client.language),
            },
        ).json()
        return response

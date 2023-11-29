from typing import List, TYPE_CHECKING, Optional

from pydantic import ConfigDict
from typing_extensions import TypedDict

from ..utils import first_not_none

if TYPE_CHECKING:
    from ..client import TmdbClient


class RequestGetTvDetails:
    class Response(TypedDict):
        __pydantic_config__ = ConfigDict(extra="allow")  # type: ignore[misc]

        name: str
        first_air_date: str
        seasons: List["RequestGetTvDetails.FieldSeasonsItem"]

    class FieldSeasonsItem(TypedDict):
        __pydantic_config__ = ConfigDict(extra="allow")  # type: ignore[misc]

        name: str
        season_number: int

    def __init__(self, tmdb_client: "TmdbClient"):
        self.tmdb_client = tmdb_client

    def __call__(
        self,
        series_id: int,
        append_to_response: Optional[str] = None,
        language: Optional[str] = None,
    ) -> "RequestGetTvDetails.Response":
        response: "RequestGetTvDetails.Response" = self.tmdb_client.session.request(
            method="GET",
            url=f"{self.tmdb_client.BASE_URL}/tv/{series_id}",
            headers=self.tmdb_client.headers,
            params={
                "api_key": self.tmdb_client.api_key,
                "append_to_response": append_to_response,
                "language": first_not_none(language, self.tmdb_client.language),
            },
        ).json()
        return response

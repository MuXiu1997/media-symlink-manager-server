from datetime import datetime
from typing import Dict, List, Any, TypeAlias, Optional

from pydantic import BaseModel, Field, field_serializer
from typing_extensions import TypedDict

from media_symlink_manager_server.models import TvModel
from media_symlink_manager_server.tmdb_client.requests import RequestGetTvDetails, RequestGetTvSeasonDetails

JsonDict: TypeAlias = Dict[str, Any]
JsonList: TypeAlias = List[Any]


class TvFilepathMapping(TypedDict):
    base_dir: str
    mappings: Dict[str, str]
    locked_keys: List[str]


class TvListItem(BaseModel):
    class Config:
        from_attributes = True

    tmdb_id: int = Field(..., description="TMDB ID", gt=0)
    name: str = Field(..., description="名称", min_length=1, max_length=255)
    year: int = Field(..., description="年份", ge=0)
    created_at: datetime = Field(..., description="创建时间")

    @field_serializer("created_at")
    def format_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")


class Tv(BaseModel):
    class Config:
        from_attributes = True

    tmdb_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    year: int = Field(..., ge=0)
    tmdb_tv: RequestGetTvDetails.Response = Field(...)
    tmdb_seasons: List[RequestGetTvSeasonDetails.Response] = Field(...)
    filepath_mapping: TvFilepathMapping = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_serializer("tmdb_tv", "tmdb_seasons", "filepath_mapping")
    def format_json(self, value: Any) -> Any:
        return value

    @field_serializer("created_at")
    def format_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def from_model(model: Optional[TvModel]) -> Optional["Tv"]:
        return Tv.model_validate(model)

    def to_model(self) -> TvModel:
        return TvModel(
            tmdb_id=self.tmdb_id,
            name=self.name,
            year=self.year,
            tmdb_tv=self.tmdb_tv,
            tmdb_seasons=self.tmdb_seasons,
            filepath_mapping=self.filepath_mapping,
            created_at=self.created_at,
        )


class FSItem(BaseModel):
    name: str
    abs_path: str
    is_dir: bool

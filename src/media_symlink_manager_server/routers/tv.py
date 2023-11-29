import os
from typing import List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pony.orm import db_session, desc  # type: ignore[import-untyped]

from media_symlink_manager_server.dependencies import tmdb_client_from_env
from media_symlink_manager_server.models import TvModel
from media_symlink_manager_server.schemas import Tv, TvListItem, TvFilepathMapping
from media_symlink_manager_server.tmdb_client.client import TmdbClient
from media_symlink_manager_server.tmdb_client.requests import (
    RequestSearchTv,
    RequestGetTvDetails,
    RequestGetTvSeasonDetails,
)
from media_symlink_manager_server.utils import avoid_invalid_filename_chars

router = APIRouter()


@router.get("/tv:search-tmdb")
async def search_tmdb_tv(
    query: str, tmdb_client: TmdbClient = Depends(tmdb_client_from_env)
) -> List[RequestSearchTv.FieldResultsItem]:
    return search_tmdb_tv_all_page(tmdb_client, query)


@router.put("/tv/{tmdb_id}", status_code=201)
async def add_tv(
    tmdb_id: int,
    tmdb_client: TmdbClient = Depends(tmdb_client_from_env),
) -> None:
    tmdb_tv, tmdb_seasons = get_tv_and_seasons(tmdb_client, tmdb_id)
    tv = Tv(
        tmdb_id=tmdb_id,
        name=tmdb_tv["name"],
        year=int(tmdb_tv["first_air_date"][:4]),
        tmdb_tv=tmdb_tv,
        tmdb_seasons=tmdb_seasons,
        filepath_mapping=init_filepath_mapping(tmdb_seasons),
    )
    with db_session:
        tv.to_model()


@router.get("/tv")
async def list_tv() -> List[TvListItem]:
    with db_session:
        return [TvListItem.model_validate(m) for m in TvModel.select().order_by(desc(TvModel.created_at))]


@router.get("/tv/{tmdb_id}")
async def get_tv(tmdb_id: int) -> Tv:
    with db_session:
        tv = Tv.from_model(TvModel.get(tmdb_id=tmdb_id))
    if tv is None:
        raise HTTPException(
            status_code=404,
            headers={"X-Error": "Not Found", "Access-Control-Expose-Headers": "X-Error"},
        )
    return tv


@router.put("/tv/{tmdb_id}/filepath-mapping", status_code=204)
async def update_tv_filepath_mapping(
    tmdb_id: int,
    filepath_mapping: TvFilepathMapping,
) -> None:
    with db_session:
        m = TvModel.get(tmdb_id=tmdb_id)
        if m is None:
            raise HTTPException(
                status_code=404,
                headers={"X-Error": "Not Found", "Access-Control-Expose-Headers": "X-Error"},
            )
        m.filepath_mapping = filepath_mapping


@router.delete("/tv/{tmdb_id}", status_code=204)
async def delete_tv(tmdb_id: int) -> None:
    with db_session:
        m = TvModel.get(tmdb_id=tmdb_id)
        if m is None:
            raise HTTPException(
                status_code=404,
                headers={"X-Error": "Not Found", "Access-Control-Expose-Headers": "X-Error"},
            )
        m.delete()


@router.post("/tv/{tmdb_id}:apply", status_code=204)
async def apply(tmdb_id: int) -> None:
    with db_session:
        tv = Tv.from_model(TvModel.get(tmdb_id=tmdb_id))
    if tv is None:
        raise HTTPException(
            status_code=404,
            headers={"X-Error": "Not Found", "Access-Control-Expose-Headers": "X-Error"},
        )

    base_dir = tv.filepath_mapping["base_dir"]
    mappings = tv.filepath_mapping["mappings"]

    tv_dirname = avoid_invalid_filename_chars(f"{tv.name} ({tv.year})")
    for season in tv.tmdb_seasons:
        season_dirname = f"Season {season['season_number']:02d}"
        season_dirpath = os.path.join(base_dir, tv_dirname, season_dirname)
        os.makedirs(season_dirpath, exist_ok=True)
        for episode in season["episodes"]:
            key = get_episode_key(episode)
            src = mappings[key]
            if src == "":
                continue
            ext = os.path.splitext(src)[1]
            dst = os.path.join(
                season_dirpath,
                avoid_invalid_filename_chars(f"{tv.name} ({tv.year}) - {key} - {episode['name']}{ext}"),
            )
            # TODO 校验 src 是否存在
            # TODO 校验是否覆盖
            if os.path.exists(dst):
                os.remove(dst)

            os.symlink(src, dst)


# region Helper functions
def search_tmdb_tv_all_page(tmdb_client: TmdbClient, query: str) -> List[RequestSearchTv.FieldResultsItem]:
    results: List[RequestSearchTv.FieldResultsItem] = list()
    page = 1
    while True:
        response = tmdb_client.search_tv(query=query, page=page, include_adult=True)
        results.extend(response["results"])
        if response["page"] >= response["total_pages"]:
            break
        page += 1
    return results


def get_tv_and_seasons(
    tmdb_client: TmdbClient,
    series_id: int,
) -> Tuple[RequestGetTvDetails.Response, List[RequestGetTvSeasonDetails.Response]]:
    tv = tmdb_client.get_tv_details(series_id=series_id)
    seasons = []
    for season in tv["seasons"]:
        season_details = tmdb_client.get_tv_season_details(
            series_id=series_id,
            season_number=season["season_number"],
        )
        seasons.append(season_details)
    return tv, seasons


def init_filepath_mapping(seasons: List[RequestGetTvSeasonDetails.Response]) -> TvFilepathMapping:
    mappings = {}
    for season in seasons:
        for episode in season["episodes"]:
            mappings[get_episode_key(episode)] = ""
    return {
        "base_dir": "/",
        "mappings": mappings,
        "locked_keys": [],
    }


def get_episode_key(episode: RequestGetTvSeasonDetails.FieldEpisodesItem) -> str:
    return f'S{episode["season_number"]:02d}E{episode["episode_number"]:02d}'


# endregion Helper functions

import os
from dataclasses import dataclass
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

    apply_tv_symlinks(tv)


# region Helper functions
@dataclass
class SymlinkTask:
    """Represents a symlink creation task."""
    src: str  # Source file path
    dst: str  # Destination symlink path


class SymlinkBatchError(Exception):
    """Raised when batch symlink creation fails due to file conflicts."""
    def __init__(self, conflicts: List[str]):
        self.conflicts = conflicts
        super().__init__(f"Files already exist: {conflicts}")


def create_symlinks_atomic(tasks: List[SymlinkTask]) -> None:
    """
    Atomically create symlinks in batch.

    - Fails if any target path is a regular file (non-symlink)
    - Allows overwriting symlinks or creating new ones

    Args:
        tasks: List of symlink creation tasks

    Raises:
        SymlinkBatchError: When regular file conflicts are detected
    """
    # Phase 1: Validate all target paths
    conflicts = []
    for task in tasks:
        if os.path.lexists(task.dst) and not os.path.islink(task.dst):
            conflicts.append(task.dst)

    if conflicts:
        raise SymlinkBatchError(conflicts)

    # Phase 2: Execute all symlink operations
    created = []
    try:
        for task in tasks:
            # Ensure destination directory exists
            dst_dir = os.path.dirname(task.dst)
            if dst_dir:
                os.makedirs(dst_dir, exist_ok=True)

            # Remove existing symlink
            if os.path.islink(task.dst):
                os.remove(task.dst)

            # Create new symlink
            os.symlink(task.src, task.dst)
            created.append(task.dst)
    except OSError:
        # Rollback created symlinks
        for dst in created:
            try:
                if os.path.islink(dst):
                    os.remove(dst)
            except OSError:
                pass
        raise


def apply_tv_symlinks(tv: Tv) -> None:
    """
    Apply TV show symlinks based on filepath mapping.

    Args:
        tv: Tv object

    Raises:
        HTTPException: 409 when file conflicts are detected
    """
    base_dir = tv.filepath_mapping["base_dir"]
    mappings = tv.filepath_mapping["mappings"]
    tv_dirname = avoid_invalid_filename_chars(f"{tv.name} ({tv.year})")

    # Collect all symlink tasks
    tasks: List[SymlinkTask] = []

    for season in tv.tmdb_seasons:
        season_dirname = f"Season {season['season_number']:02d}"
        season_dirpath = os.path.join(base_dir, tv_dirname, season_dirname)

        for episode in season["episodes"]:
            key = get_episode_key(episode)
            src = mappings.get(key, "")
            if src == "":
                continue

            ext = os.path.splitext(src)[1]
            dst = os.path.join(
                season_dirpath,
                avoid_invalid_filename_chars(f"{tv.name} ({tv.year}) - {key} - {episode['name']}{ext}"),
            )
            tasks.append(SymlinkTask(src=src, dst=dst))

    # Execute atomically
    try:
        create_symlinks_atomic(tasks)
    except SymlinkBatchError as e:
        raise HTTPException(
            status_code=409,
            headers={
                "X-Error": f"Files already exist: {', '.join(e.conflicts)}",
                "Access-Control-Expose-Headers": "X-Error",
            },
        )


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

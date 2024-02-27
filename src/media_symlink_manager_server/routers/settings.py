from typing import Dict, Any

from fastapi import APIRouter

from media_symlink_manager_server import settings

router = APIRouter()


@router.get("/settings")
async def get_settings() -> Dict[str, Any]:
    return {
        "target_base_dir_options": settings.TARGET_BASE_DIR_OPTIONS,
        "fs_select_base_dir": settings.FS_SELECT_BASE_DIR,
    }

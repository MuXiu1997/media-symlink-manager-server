import os
from typing import List

from fastapi import APIRouter

from media_symlink_manager_server.schemas import FSItem

router = APIRouter()


@router.get("/fs:ls")
async def list_dir(abs_path: str) -> List[FSItem]:
    dir_items = []
    file_items = []

    for name in sorted(os.listdir(abs_path)):
        item_abs_path = os.path.join(abs_path, name)
        is_dir = os.path.isdir(item_abs_path)
        item = FSItem(name=name, abs_path=item_abs_path, is_dir=is_dir)
        if is_dir:
            dir_items.append(item)
        else:
            file_items.append(item)
    return dir_items + file_items

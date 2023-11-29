from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from media_symlink_manager_server.dependencies import setup_db_from_env
from media_symlink_manager_server.routers import tv, fs


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_db_from_env()
    yield


app = FastAPI(lifespan=lifespan)

# Allow CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(tv.router, prefix="/api")
app.include_router(fs.router, prefix="/api")
app.mount("/", StaticFiles(packages=[__name__], html=True))

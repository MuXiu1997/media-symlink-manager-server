import fire  # type: ignore[import-untyped]
import uvicorn

from media_symlink_manager_server import app


def cmd(host: str = "0.0.0.0", port: int = 80) -> None:
    uvicorn.run(
        app=app,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    fire.Fire(cmd)

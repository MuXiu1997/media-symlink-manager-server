import fire  # type: ignore[import-untyped]

APP_STR = "media_symlink_manager_server:app"


def dev() -> None:
    import uvicorn

    def cmd(host: str = "0.0.0.0", port: int = 8080) -> None:
        uvicorn.run(
            app=APP_STR,
            host=host,
            port=port,
            reload=True,
        )

    fire.Fire(cmd)


def build() -> None:
    import subprocess

    def cmd() -> None:
        subprocess.run(
            [
                "python3",
                "-m",
                "nuitka",
                "--follow-imports",
                "--onefile",
                "--include-module=pydantic",
                "--include-package=pony.orm.dbproviders",
                "--include-package-data=media_symlink_manager_server",
                "--output-dir=dist",
                "--output-filename=media-symlink-manager",
                "--assume-yes-for-downloads",
                "main.py",
            ]
        )

    fire.Fire(cmd)


if __name__ == "__main__":
    dev()

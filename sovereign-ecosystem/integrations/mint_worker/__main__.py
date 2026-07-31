"""Run: python -m integrations.mint_worker from repo root."""

from __future__ import annotations

import uvicorn

from .server import app


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8090)


if __name__ == "__main__":
    main()

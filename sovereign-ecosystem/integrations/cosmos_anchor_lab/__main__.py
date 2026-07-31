"""Run lab Cosmos anchor REST stub: python -m integrations.cosmos_anchor_lab"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("COSMOS_ANCHOR_LAB_HOST", "127.0.0.1")
    port = int(os.environ.get("COSMOS_ANCHOR_LAB_PORT", "1317"))
    uvicorn.run(
        "integrations.cosmos_anchor_lab.server:app",
        host=host,
        port=port,
        log_level=os.environ.get("COSMOS_ANCHOR_LAB_LOG", "info"),
    )


if __name__ == "__main__":
    main()

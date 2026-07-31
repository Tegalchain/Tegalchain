"""Legacy Qortal tx.pl submitter (optional — not required for Replit lab)."""

from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any

from .config import SubmitterConfig


def submit_to_qortal(block_candidate: dict[str, Any], config: SubmitterConfig) -> str:
    if not config.privkey:
        raise RuntimeError("TEGALCHAIN_PRIVKEY is not configured")
    if not config.tx_pl_path.is_file():
        raise RuntimeError(f"tx.pl not found at {config.tx_pl_path}")

    data = json.dumps(block_candidate, separators=(",", ":"), sort_keys=True)
    env = {**os.environ, "BASE_URL": config.api_url.rstrip("/")}
    result = subprocess.run(
        [
            "perl",
            str(config.tx_pl_path),
            "-p",
            "arbitrary",
            config.privkey,
            config.qortal_service,
            config.qortal_data_type,
            data,
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"tx.pl failed ({result.returncode}): {result.stderr or result.stdout}"
        )

    output = result.stdout + result.stderr
    match = re.search(r"Signature:\s*(\S+)", output)
    if not match:
        raise RuntimeError(f"tx.pl succeeded but no signature found: {output}")
    return match.group(1)

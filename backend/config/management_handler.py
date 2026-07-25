"""Lambda handler for running Django management commands.

Usage:
    aws lambda invoke --function-name skill-worker \
        --payload '{"command": "migrate"}' \
        --cli-binary-format raw-in-base64-out \
        response.json
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Invoke a Django management command from Lambda event payload."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

    command = event.get("command", "")
    args: list[str] = event.get("args", [])

    if not command:
        return {"statusCode": 400, "body": "Missing 'command' field"}

    full_command = [sys.executable, "manage.py", command, *args]
    logger.info("Executing: %s", " ".join(full_command))

    result = subprocess.run(  # noqa: S603
        full_command,
        capture_output=True,
        text=True,
        timeout=870,
    )

    if result.returncode == 0:
        logger.info("Command '%s' succeeded. stdout: %s", command, result.stdout[-1000:])
    else:
        logger.error("Command '%s' failed (rc=%d). stderr: %s", command, result.returncode, result.stderr[-2000:])

    return {
        "statusCode": 0 if result.returncode == 0 else 1,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "returncode": result.returncode,
    }

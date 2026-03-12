"""Safe subprocess utilities."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    timeout: Optional[int] = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess command safely.

    Args:
        cmd: Command and arguments as a list.
        cwd: Working directory.
        env: Environment variables (merged with current environment if None).
        timeout: Timeout in seconds.
        check: Raise CalledProcessError on non-zero exit code.
        capture_output: Capture stdout and stderr.

    Returns:
        CompletedProcess instance.

    Raises:
        subprocess.CalledProcessError: If check=True and exit code != 0.
        subprocess.TimeoutExpired: If timeout is exceeded.
    """
    logger.debug("Running: %s", " ".join(str(c) for c in cmd))
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        timeout=timeout,
        check=False,
        capture_output=capture_output,
        text=True,
    )
    if check and result.returncode != 0:
        logger.error("Command failed (exit %d): %s", result.returncode, " ".join(str(c) for c in cmd))
        if result.stderr:
            logger.error("stderr:\n%s", result.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def which(executable: str) -> Optional[str]:
    """Return the path to *executable*, or None if not found on PATH."""
    import shutil  # noqa: PLC0415

    return shutil.which(executable)


def require_executable(name: str, install_hint: str = "") -> str:
    """Return path to *name* or raise RuntimeError with install guidance."""
    path = which(name)
    if path is None:
        msg = f"'{name}' not found on PATH."
        if install_hint:
            msg += f" {install_hint}"
        raise RuntimeError(msg)
    return path


def stream_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Run *cmd* and stream output to the logger in real time.

    Returns:
        Exit code.
    """
    logger.debug("Streaming: %s", " ".join(str(c) for c in cmd))
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in process.stdout:  # type: ignore[union-attr]
        logger.info(line.rstrip())
    process.wait()
    return process.returncode

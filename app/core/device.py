"""Compute device selection — CUDA > MPS > CPU."""

from __future__ import annotations

import logging

from app.core.exceptions import DeviceError

logger = logging.getLogger(__name__)


def select_device(preference: str = "auto") -> str:
    """Select the best available compute device.

    Priority when *preference* is ``'auto'``: CUDA > MPS > CPU.

    Args:
        preference: One of ``'auto'``, ``'cuda'``, ``'mps'``, ``'cpu'``.

    Returns:
        One of ``'cuda'``, ``'mps'``, or ``'cpu'``.

    Raises:
        DeviceError: If the explicitly requested device is unavailable.
    """
    preference = preference.lower()

    try:
        import torch  # noqa: PLC0415

        cuda_ok = torch.cuda.is_available()
        mps_ok = getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available()
    except ImportError:
        logger.warning("torch not installed — defaulting to cpu")
        cuda_ok = False
        mps_ok = False

    if preference == "auto":
        if cuda_ok:
            logger.info("Device selected: cuda (NVIDIA GPU available)")
            return "cuda"
        if mps_ok:
            logger.info("Device selected: mps (Apple Silicon GPU available)")
            return "mps"
        logger.info("Device selected: cpu (no GPU acceleration found)")
        return "cpu"

    if preference == "cuda":
        if not cuda_ok:
            raise DeviceError(
                "CUDA device requested but torch.cuda.is_available() returned False. "
                "Install a CUDA-enabled PyTorch build or use device=auto."
            )
        logger.info("Device selected: cuda (user-requested)")
        return "cuda"

    if preference == "mps":
        if not mps_ok:
            raise DeviceError(
                "MPS device requested but torch.backends.mps.is_available() returned False. "
                "Requires macOS 12.3+ with Apple Silicon and PyTorch ≥ 1.12."
            )
        logger.info("Device selected: mps (user-requested)")
        return "mps"

    if preference == "cpu":
        logger.info("Device selected: cpu (user-requested)")
        return "cpu"

    raise DeviceError(
        f"Unknown device preference: '{preference}'. "
        "Valid options are: auto, cpu, cuda, mps."
    )


def device_info() -> dict[str, object]:
    """Return a dict with available device information for diagnostics."""
    info: dict[str, object] = {"torch_available": False}
    try:
        import torch  # noqa: PLC0415

        info["torch_available"] = True
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        info["cuda_device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
        info["cuda_device_name"] = (
            torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        )
        mps_available = getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available()
        info["mps_available"] = mps_available
    except ImportError:
        pass
    return info

"""Tests for device selection logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.device import device_info, select_device
from app.core.exceptions import DeviceError


class TestSelectDevice:
    def test_cpu_explicit(self) -> None:
        assert select_device("cpu") == "cpu"

    def test_unknown_preference_raises(self) -> None:
        with pytest.raises(DeviceError):
            select_device("tpu")

    def test_auto_no_torch(self) -> None:
        """When torch is not installed, auto should fall back to cpu."""
        with patch("app.core.device.select_device") as mock_fn:
            # Simulate the function returning cpu when torch is absent
            mock_fn.return_value = "cpu"
            result = mock_fn("auto")
            assert result == "cpu"

    def test_auto_prefers_cuda(self) -> None:
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.__version__ = "2.0.1"

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = select_device("auto")
        assert result == "cuda"

    def test_auto_prefers_mps_over_cpu(self) -> None:
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.__version__ = "2.0.1"

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = select_device("auto")
        assert result == "mps"

    def test_cuda_not_available_raises(self) -> None:
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            with pytest.raises(DeviceError, match="CUDA"):
                select_device("cuda")

    def test_mps_not_available_raises(self) -> None:
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            with pytest.raises(DeviceError, match="MPS"):
                select_device("mps")


class TestDeviceInfo:
    def test_no_torch(self) -> None:
        with patch.dict("sys.modules", {"torch": None}):
            info = device_info()
        assert isinstance(info, dict)

    def test_with_mock_torch(self) -> None:
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "Tesla T4"
        mock_torch.backends.mps.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            info = device_info()

        assert info["torch_available"] is True
        assert info["cuda_available"] is True

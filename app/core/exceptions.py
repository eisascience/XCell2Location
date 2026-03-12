"""Custom exception hierarchy for XCell2Location."""


class XCellError(Exception):
    """Base exception for all XCell2Location errors."""


class ConfigError(XCellError):
    """Raised when configuration is invalid or missing."""


class AtlasError(XCellError):
    """Raised on atlas registration, download, or validation failures."""


class DeviceError(XCellError):
    """Raised when the requested compute device is unavailable."""


class IOError(XCellError):  # noqa: A001  (shadows built-in intentionally)
    """Raised on file I/O failures (read, write, parse)."""


class BackendError(XCellError):
    """Raised when a model backend encounters an error during setup or inference."""


class ManifestError(XCellError):
    """Raised when manifest generation or serialization fails."""


class ValidationError(XCellError):
    """Raised when input data fails validation checks."""

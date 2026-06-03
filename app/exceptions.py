class ScannerError(Exception):
    """Base exception for the scanner."""
    pass

class WatchlistError(ScannerError):
    """Raised when there is an issue with the watchlist."""
    pass

class ProviderError(ScannerError):
    """Raised when a data provider fails."""
    pass

class ConfigurationError(ScannerError):
    """Raised when configuration is invalid."""
    pass

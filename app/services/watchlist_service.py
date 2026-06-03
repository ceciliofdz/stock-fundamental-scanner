import yaml
from pathlib import Path
from app.models import WatchlistSymbol
from app.exceptions import WatchlistError

class WatchlistService:
    def __init__(self, watchlist_path: Path):
        self.watchlist_path = watchlist_path

    def load_watchlist(self) -> list[WatchlistSymbol]:
        if not self.watchlist_path.exists():
            raise WatchlistError(f"Watchlist file not found at {self.watchlist_path}")

        try:
            with open(self.watchlist_path, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise WatchlistError(f"Failed to parse watchlist YAML: {e}")

        if not data or "symbols" not in data:
            raise WatchlistError("Watchlist YAML must contain a 'symbols' key")

        symbols_data = data["symbols"]
        if not isinstance(symbols_data, list):
            raise WatchlistError("'symbols' must be a list")

        processed_symbols: dict[str, WatchlistSymbol] = {}
        
        for item in symbols_data:
            if isinstance(item, str):
                symbol = item.strip().upper()
                if symbol:
                    # Keep existing or add new enabled
                    if symbol not in processed_symbols:
                        processed_symbols[symbol] = WatchlistSymbol(symbol=symbol, enabled=True)
            elif isinstance(item, dict):
                symbol = item.get("symbol")
                if not symbol or not isinstance(symbol, str):
                    continue
                symbol = symbol.strip().upper()
                enabled = item.get("enabled", True)
                # If already exists, we might want to override or skip. 
                # Requirements say: remove duplicates. We'll take the first enabled one if duplicates exist, 
                # or just use the last seen definition.
                processed_symbols[symbol] = WatchlistSymbol(symbol=symbol, enabled=enabled)
            else:
                continue

        # Filter out disabled and empty
        final_list = [ws for ws in processed_symbols.values() if ws.enabled]
        
        if not final_list:
            raise WatchlistError("Watchlist is empty after processing")

        return final_list

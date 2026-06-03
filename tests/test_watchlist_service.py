import pytest
import yaml
from pathlib import Path
from app.services.watchlist_service import WatchlistService
from app.exceptions import WatchlistError

def test_load_watchlist_simple(tmp_path):
    d = tmp_path / "config"
    d.mkdir()
    p = d / "watchlist.yaml"
    p.write_text("symbols:\n  - AAPL\n  - nvda\n  - AAPL")
    
    service = WatchlistService(p)
    watchlist = service.load_watchlist()
    
    assert len(watchlist) == 2
    assert watchlist[0].symbol == "AAPL"
    assert watchlist[1].symbol == "NVDA"

def test_load_watchlist_extended(tmp_path):
    p = tmp_path / "watchlist.yaml"
    content = {
        "symbols": [
            {"symbol": "AAPL", "enabled": True},
            {"symbol": "TSLA", "enabled": False},
            "AMD"
        ]
    }
    p.write_text(yaml.dump(content))
    
    service = WatchlistService(p)
    watchlist = service.load_watchlist()
    
    assert len(watchlist) == 2
    symbols = [ws.symbol for ws in watchlist]
    assert "AAPL" in symbols
    assert "AMD" in symbols
    assert "TSLA" not in symbols

def test_load_watchlist_empty(tmp_path):
    p = tmp_path / "watchlist.yaml"
    p.write_text("symbols: []")
    
    service = WatchlistService(p)
    with pytest.raises(WatchlistError, match="empty after processing"):
        service.load_watchlist()

def test_load_watchlist_missing_file():
    service = WatchlistService(Path("non_existent.yaml"))
    with pytest.raises(WatchlistError, match="not found"):
        service.load_watchlist()

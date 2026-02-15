"""
ClaudeHedge Data Pipeline Manager
Comprehensive data fetching, cleaning, and caching system

This module manages the entire data pipeline for ClaudeHedge:
- Multi-source data fetching with fallbacks
- Real-time and historical data retrieval
- Data validation and cleaning
- Caching for performance optimization
- Market calendar awareness
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple, Optional, Union
import yfinance as yf
import requests
import pickle
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class DataPipelineManager:
    """
    Comprehensive data pipeline for ClaudeHedge strategy.
    
    Handles data acquisition, validation, cleaning, and caching for
    Nikkei 225, DAX, and Nasdaq futures markets.
    """
    
    def __init__(self, cache_dir: str = 'data/cache'):
        """
        Initialize data pipeline manager.
        
        Args:
            cache_dir: Directory for caching downloaded data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Market configurations
        self.markets = {
            'Nikkei': {
                'ticker': 'NKD=F',
                'alternative_tickers': ['^N225', 'NI225'],
                'timezone': 'Asia/Tokyo',
                'session_start': time(19, 0),  # 7 PM ET
                'session_end': time(3, 0),     # 3 AM ET (next day)
                'point_value': 5.0,
                'tick_size': 5.0
            },
            'DAX': {
                'ticker': 'FDAX=F',
                'alternative_tickers': ['^GDAXI', 'DAX'],
                'timezone': 'Europe/Frankfurt',
                'session_start': time(3, 0),   # 3 AM ET
                'session_end': time(11, 0),    # 11 AM ET
                'point_value': 25.0,
                'tick_size': 0.5
            },
            'Nasdaq': {
                'ticker': 'NQ=F',
                'alternative_tickers': ['^IXIC', 'NDX'],
                'timezone': 'America/New_York',
                'session_start': time(11, 0),  # 11 AM ET
                'session_end': time(19, 0),    # 7 PM ET
                'point_value': 20.0,
                'tick_size': 0.25
            }
        }
        
        # Data sources priority
        self.data_sources = ['yfinance', 'yahoo_backup', 'cache']
        
        # Cache settings
        self.cache_expiry_hours = 24
        
        print(f"DataPipelineManager initialized")
        print(f"Cache directory: {self.cache_dir}")
        print(f"Markets configured: {list(self.markets.keys())}")
        
    def fetch_historical_data(
        self,
        market: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = '5m',
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical market data with caching and fallbacks.
        
        Args:
            market: Market name ('Nikkei', 'DAX', 'Nasdaq')
            start_date: Start date
            end_date: End date  
            interval: Data interval ('1m', '5m', '15m', '1h', '1d')
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with OHLCV data
        """
        # Check cache first
        if use_cache:
            cached_data = self._load_from_cache(market, start_date, end_date, interval)
            if cached_data is not None:
                print(f"Loaded {market} data from cache")
                return cached_data
                
        # Try primary source
        data = self._fetch_from_yfinance(market, start_date, end_date, interval)
        
        # Fallback to alternative tickers if primary fails
        if data.empty:
            print(f"Primary ticker failed for {market}, trying alternatives...")
            data = self._fetch_from_alternatives(market, start_date, end_date, interval)
            
        # Validate and clean data
        if not data.empty:
            data = self._validate_data(data, market)
            data = self._clean_data(data)
            
            # Cache the data
            if use_cache:
                self._save_to_cache(data, market, start_date, end_date, interval)
                
        return data
        
    def fetch_session_data(
        self,
        market: str,
        date: datetime,
        interval: str = '5m'
    ) -> pd.DataFrame:
        """
        Fetch data for specific market session.
        
        Args:
            market: Market name
            date: Trading date
            interval: Data interval
            
        Returns:
            DataFrame with session data
        """
        config = self.markets[market]
        
        # Calculate session window
        session_start = datetime.combine(date.date(), config['session_start'])
        session_end = datetime.combine(date.date(), config['session_end'])
        
        # Handle overnight sessions
        if session_end < session_start:
            session_end += timedelta(days=1)
            
        # Fetch data with buffer
        start_buffer = session_start - timedelta(hours=2)
        end_buffer = session_end + timedelta(hours=2)
        
        data = self.fetch_historical_data(
            market, 
            start_buffer, 
            end_buffer, 
            interval
        )
        
        if data.empty:
            return pd.DataFrame()
            
        # Filter to exact session
        mask = (data.index >= session_start) & (data.index <= session_end)
        session_data = data[mask].copy()
        
        return session_data
        
    def _fetch_from_yfinance(
        self,
        market: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str
    ) -> pd.DataFrame:
        """Fetch data from yfinance."""
        ticker = self.markets[market]['ticker']
        
        try:
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False,
                auto_adjust=True
            )
            
            if not data.empty:
                # Standardize column names
                data.columns = [col[0] if isinstance(col, tuple) else col 
                               for col in data.columns]
                               
            return data
            
        except Exception as e:
            print(f"Error fetching from yfinance: {e}")
            return pd.DataFrame()
            
    def _fetch_from_alternatives(
        self,
        market: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str
    ) -> pd.DataFrame:
        """Try alternative tickers as fallback."""
        alternative_tickers = self.markets[market]['alternative_tickers']
        
        for ticker in alternative_tickers:
            try:
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    progress=False
                )
                
                if not data.empty:
                    print(f"Successfully fetched {market} using {ticker}")
                    return data
                    
            except Exception as e:
                print(f"Failed to fetch {ticker}: {e}")
                continue
                
        return pd.DataFrame()
        
    def _validate_data(self, data: pd.DataFrame, market: str) -> pd.DataFrame:
        """
        Validate data quality and completeness.
        
        Args:
            data: Raw data
            market: Market name
            
        Returns:
            Validated data
        """
        if data.empty:
            return data
            
        # Check required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        
        if missing_cols:
            print(f"Warning: Missing columns for {market}: {missing_cols}")
            return pd.DataFrame()
            
        # Check for sufficient data
        if len(data) < 10:
            print(f"Warning: Insufficient data for {market} ({len(data)} bars)")
            
        # Validate OHLC relationships
        invalid_hl = (data['High'] < data['Low']).sum()
        if invalid_hl > 0:
            print(f"Warning: {invalid_hl} bars with High < Low")
            
        # Check for extreme outliers
        returns = data['Close'].pct_change()
        extreme_moves = (returns.abs() > 0.20).sum()  # >20% moves
        if extreme_moves > 0:
            print(f"Warning: {extreme_moves} extreme price movements detected")
            
        return data
        
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess data.
        
        Args:
            data: Raw data
            
        Returns:
            Cleaned data
        """
        if data.empty:
            return data
            
        # Create a copy
        cleaned = data.copy()
        
        # Fix OHLC relationships
        # Ensure High >= Low
        mask = cleaned['High'] < cleaned['Low']
        if mask.any():
            cleaned.loc[mask, ['High', 'Low']] = \
                cleaned.loc[mask, ['Low', 'High']].values
                
        # Ensure Close within High-Low range
        cleaned['Close'] = cleaned['Close'].clip(
            lower=cleaned['Low'],
            upper=cleaned['High']
        )
        
        # Remove obvious errors (prices <= 0)
        cleaned = cleaned[cleaned['Close'] > 0].copy()
        
        # Handle missing values
        if cleaned.isnull().any().any():
            # Forward fill first
            cleaned = cleaned.fillna(method='ffill')
            # Then backward fill any remaining
            cleaned = cleaned.fillna(method='bfill')
            # Drop if still have nulls
            cleaned = cleaned.dropna()
            
        # Remove duplicate timestamps
        cleaned = cleaned[~cleaned.index.duplicated(keep='first')]
        
        # Sort by index
        cleaned = cleaned.sort_index()
        
        return cleaned
        
    def _get_cache_path(
        self,
        market: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str
    ) -> Path:
        """Generate cache file path."""
        start_str = pd.to_datetime(start_date).strftime('%Y%m%d')
        end_str = pd.to_datetime(end_date).strftime('%Y%m%d')
        
        filename = f"{market}_{start_str}_{end_str}_{interval}.pkl"
        return self.cache_dir / filename
        
    def _load_from_cache(
        self,
        market: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str
    ) -> Optional[pd.DataFrame]:
        """Load data from cache if available and fresh."""
        cache_path = self._get_cache_path(market, start_date, end_date, interval)
        
        if not cache_path.exists():
            return None
            
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(
            cache_path.stat().st_mtime
        )
        
        if cache_age > timedelta(hours=self.cache_expiry_hours):
            print(f"Cache expired for {market} ({cache_age.total_seconds()/3600:.1f} hours old)")
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None
            
    def _save_to_cache(
        self,
        data: pd.DataFrame,
        market: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str
    ):
        """Save data to cache."""
        cache_path = self._get_cache_path(market, start_date, end_date, interval)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            print(f"Cached {market} data to {cache_path.name}")
        except Exception as e:
            print(f"Error saving cache: {e}")
            
    def fetch_vix(self, date: datetime) -> float:
        """
        Fetch VIX level for given date.
        
        Args:
            date: Date to fetch VIX
            
        Returns:
            VIX close value
        """
        try:
            vix = yf.Ticker('^VIX')
            data = vix.history(
                start=date - timedelta(days=5),
                end=date + timedelta(days=1)
            )
            
            if not data.empty:
                return float(data['Close'].iloc[-1])
            else:
                return 20.0  # Default VIX
                
        except Exception as e:
            print(f"Error fetching VIX: {e}")
            return 20.0
            
    def clear_cache(self, market: Optional[str] = None):
        """
        Clear cached data.
        
        Args:
            market: Specific market to clear, or None for all
        """
        if market:
            pattern = f"{market}_*.pkl"
        else:
            pattern = "*.pkl"
            
        removed = 0
        for cache_file in self.cache_dir.glob(pattern):
            cache_file.unlink()
            removed += 1
            
        print(f"Cleared {removed} cache files")
        
    def get_market_info(self, market: str) -> Dict:
        """Get market configuration."""
        return self.markets.get(market, {})
        
    def is_market_open(self, market: str, timestamp: datetime) -> bool:
        """
        Check if market is open at given timestamp.
        
        Args:
            market: Market name
            timestamp: Time to check
            
        Returns:
            True if market is open
        """
        config = self.markets[market]
        current_time = timestamp.time()
        
        session_start = config['session_start']
        session_end = config['session_end']
        
        # Handle overnight sessions
        if session_end < session_start:
            return current_time >= session_start or current_time < session_end
        else:
            return session_start <= current_time < session_end


if __name__ == '__main__':
    # Example usage
    pipeline = DataPipelineManager()
    
    # Fetch recent data for all markets
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    for market in ['Nikkei', 'DAX', 'Nasdaq']:
        print(f"\n{'='*60}")
        print(f"Fetching {market} data...")
        print(f"{'='*60}")
        
        data = pipeline.fetch_historical_data(
            market,
            start_date,
            end_date,
            interval='1h'
        )
        
        if not data.empty:
            print(f"\nData shape: {data.shape}")
            print(f"Date range: {data.index[0]} to {data.index[-1]}")
            print(f"\nFirst 5 rows:")
            print(data.head())
        else:
            print(f"No data available for {market}")

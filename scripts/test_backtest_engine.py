"""
Unit Tests for Backtest Engine
Comprehensive test suite for backtesting functionality
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBacktestEngine:
    """Test suite for BacktestEngine class."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample market data for testing."""
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        data = pd.DataFrame({
            'Open': 100 + np.random.randn(100).cumsum(),
            'High': 101 + np.random.randn(100).cumsum(),
            'Low': 99 + np.random.randn(100).cumsum(),
            'Close': 100 + np.random.randn(100).cumsum(),
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Ensure OHLC relationships
        data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
        data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
        
        return data
    
    def test_initialization(self):
        """Test engine initialization."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-12-31',
            initial_capital=100000
        )
        
        assert engine.initial_capital == 100000
        assert engine.capital == 100000
        assert len(engine.trades) == 0
        
    def test_position_sizing(self):
        """Test VIX-adaptive position sizing."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        # Test low VIX
        size_low = engine.calculate_position_size(vix_level=12, market='Nikkei')
        assert size_low == 100000 * 0.95  # Full size
        
        # Test medium VIX
        size_med = engine.calculate_position_size(vix_level=20, market='DAX')
        assert size_med == 100000 * 0.95 * 0.75  # Reduced size
        
        # Test high VIX
        size_high = engine.calculate_position_size(vix_level=40, market='Nasdaq')
        assert size_high == 100000 * 0.95 * 0.30  # Minimal size
        
    def test_session_execution(self, sample_data):
        """Test single session execution."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-01-02'
        )
        
        result = engine.execute_session(
            market='Nikkei',
            date=datetime(2024, 1, 1),
            vix=20.0
        )
        
        assert 'market' in result
        assert 'return' in result
        assert 'pnl' in result
        
    def test_backtest_execution(self):
        """Test complete backtest run."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-01-10',
            initial_capital=100000
        )
        
        results = engine.run_backtest()
        
        assert isinstance(results, pd.DataFrame)
        assert len(results) > 0
        assert 'market' in results.columns
        assert 'pnl' in results.columns
        
    def test_metrics_calculation(self):
        """Test performance metrics calculation."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-12-31',
            initial_capital=100000
        )
        
        # Run backtest
        engine.run_backtest()
        
        # Calculate metrics
        metrics = engine.calculate_metrics()
        
        assert 'Total Return' in metrics
        assert 'CAGR' in metrics
        assert 'Sharpe Ratio' in metrics
        assert 'Max Drawdown' in metrics
        assert 'Win Rate' in metrics
        
    def test_commission_calculation(self):
        """Test commission and slippage application."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-01-10',
            commission_rate=0.001,  # 10 bps
            slippage_bps=2
        )
        
        results = engine.run_backtest()
        
        # Verify commissions were applied
        assert engine.commission_rate == 0.001
        assert engine.slippage_bps == 2
        
    def test_market_config(self):
        """Test market configuration."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-01-10'
        )
        
        # Verify market configs exist
        assert 'Nikkei' in engine.market_config
        assert 'DAX' in engine.market_config
        assert 'Nasdaq' in engine.market_config
        
        # Verify config structure
        nikkei_config = engine.market_config['Nikkei']
        assert 'ticker' in nikkei_config
        assert 'session_start' in nikkei_config
        assert 'session_end' in nikkei_config
        
    def test_vix_fetch(self):
        """Test VIX data fetching."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-01-10'
        )
        
        vix = engine.fetch_vix(datetime(2024, 1, 5))
        
        assert isinstance(vix, float)
        assert vix > 0
        assert vix < 100  # Reasonable VIX range
        
    def test_export_results(self):
        """Test results export to CSV."""
        import os
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-01-10'
        )
        
        engine.run_backtest()
        
        # Export
        filename = '/tmp/test_backtest_results.csv'
        engine.export_results(filename)
        
        # Verify file exists
        assert os.path.exists(filename)
        
        # Verify content
        df = pd.read_csv(filename)
        assert len(df) > 0
        assert 'market' in df.columns
        
        # Cleanup
        os.remove(filename)


class TestBacktestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_capital(self):
        """Test handling of zero capital."""
        from backtest_engine import BacktestEngine
        
        with pytest.raises(ValueError):
            engine = BacktestEngine(
                start_date='2024-01-01',
                end_date='2024-01-10',
                initial_capital=0
            )
    
    def test_invalid_dates(self):
        """Test invalid date ranges."""
        from backtest_engine import BacktestEngine
        
        # End before start
        engine = BacktestEngine(
            start_date='2024-12-31',
            end_date='2024-01-01'
        )
        
        results = engine.run_backtest()
        assert len(results) == 0
        
    def test_missing_data(self):
        """Test handling of missing market data."""
        from backtest_engine import BacktestEngine
        
        engine = BacktestEngine(
            start_date='2024-01-01',
            end_date='2024-01-10'
        )
        
        # This should handle missing data gracefully
        result = engine.execute_session(
            market='Nikkei',
            date=datetime(2050, 1, 1),  # Future date
            vix=20.0
        )
        
        assert result['reason'] == 'No data'
        assert result['return'] == 0.0


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])

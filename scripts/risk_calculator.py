"""
ClaudeHedge Risk Calculator
Comprehensive risk analysis and position sizing calculations

Provides tools for:
- Kelly Criterion position sizing
- Risk of ruin calculations
- Portfolio heat monitoring
- Correlation analysis across markets
- Exposure management
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.optimize import minimize_scalar
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')


class RiskCalculator:
    """
    Advanced risk calculation and management system.
    
    Handles position sizing, risk metrics, and exposure management
    for the ClaudeHedge multi-market strategy.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,
        max_position_size: float = 0.95,
        max_portfolio_risk: float = 0.10,
        max_correlation_exposure: float = 0.50
    ):
        """
        Initialize risk calculator.
        
        Args:
            initial_capital: Starting capital
            max_position_size: Maximum position as % of capital
            max_portfolio_risk: Maximum portfolio risk as % of capital
            max_correlation_exposure: Max exposure to correlated positions
        """
        self.initial_capital = initial_capital
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlation_exposure = max_correlation_exposure
        
        # Market correlation matrix (approximate historical)
        self.correlation_matrix = pd.DataFrame({
            'Nikkei': [1.00, 0.65, 0.70],
            'DAX': [0.65, 1.00, 0.85],
            'Nasdaq': [0.70, 0.85, 1.00]
        }, index=['Nikkei', 'DAX', 'Nasdaq'])
        
        print(f"RiskCalculator initialized")
        print(f"Max position size: {max_position_size*100}%")
        print(f"Max portfolio risk: {max_portfolio_risk*100}%")
        
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        kelly_fraction: float = 0.25
    ) -> float:
        """
        Calculate Kelly Criterion position size.
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade %
            avg_loss: Average losing trade % (positive number)
            kelly_fraction: Fraction of Kelly to use (default 25%)
            
        Returns:
            Optimal position size as decimal
        """
        if win_rate <= 0 or win_rate >= 1:
            return 0.0
            
        if avg_loss <= 0:
            return 0.0
            
        # Kelly formula: f = (p*b - q) / b
        # where p = win rate, q = loss rate, b = win/loss ratio
        win_loss_ratio = avg_win / avg_loss
        
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Apply fractional Kelly (more conservative)
        fractional_kelly = kelly * kelly_fraction
        
        # Cap at max position size
        position_size = min(fractional_kelly, self.max_position_size)
        
        return max(0, position_size)
        
    def optimal_f(
        self,
        trades: pd.Series,
        starting_capital: float = None
    ) -> float:
        """
        Calculate Optimal F (optimal fixed fraction).
        
        Args:
            trades: Series of trade P&Ls
            starting_capital: Starting capital for calculation
            
        Returns:
            Optimal position size fraction
        """
        if starting_capital is None:
            starting_capital = self.initial_capital
            
        def terminal_wealth(f):
            """Calculate terminal wealth for given f."""
            if f <= 0 or f >= 1:
                return -1e10
                
            wealth = starting_capital
            for trade_pnl in trades:
                wealth = wealth * (1 + f * (trade_pnl / starting_capital))
                if wealth <= 0:
                    return -1e10
            return -wealth  # Negative for minimization
            
        # Find f that maximizes terminal wealth
        result = minimize_scalar(
            terminal_wealth,
            bounds=(0.01, 0.99),
            method='bounded'
        )
        
        optimal = result.x
        
        # Apply safety margin
        conservative_f = optimal * 0.5
        
        return min(conservative_f, self.max_position_size)
        
    def risk_of_ruin(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        capital: float,
        max_loss: float
    ) -> float:
        """
        Calculate risk of ruin (probability of losing max_loss).
        
        Args:
            win_rate: Win rate
            avg_win: Average win size
            avg_loss: Average loss size
            capital: Current capital
            max_loss: Maximum acceptable loss
            
        Returns:
            Probability of ruin (0-1)
        """
        if win_rate >= 1 or win_rate <= 0:
            return 0.0 if win_rate >= 1 else 1.0
            
        # Calculate advantage
        expected_value = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        if expected_value <= 0:
            return 1.0  # Negative expectancy = certain ruin
            
        # Risk of ruin formula
        loss_units = max_loss / avg_loss
        win_loss_ratio = avg_win / avg_loss
        
        p = win_rate
        q = 1 - win_rate
        
        if abs(win_loss_ratio - 1) < 1e-10:
            # When win/loss ratio = 1
            ror = ((1 - p) / p) ** loss_units
        else:
            # General case
            ror = ((q / p) * (win_loss_ratio)) ** loss_units
            
        return min(1.0, max(0.0, ror))
        
    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
        holding_period: int = 1
    ) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Historical returns
            confidence: Confidence level (e.g., 0.95 for 95%)
            holding_period: Holding period in days
            
        Returns:
            VaR as decimal (negative = loss)
        """
        # Parametric VaR
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Z-score for confidence level
        z_score = norm.ppf(1 - confidence)
        
        # VaR calculation
        var = mean_return + (z_score * std_return * np.sqrt(holding_period))
        
        return var
        
    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR/Expected Shortfall).
        
        Args:
            returns: Historical returns
            confidence: Confidence level
            
        Returns:
            CVaR as decimal (negative = loss)
        """
        var_threshold = np.percentile(returns, (1 - confidence) * 100)
        cvar = returns[returns <= var_threshold].mean()
        return cvar
        
    def position_size_atr(
        self,
        account_balance: float,
        atr: float,
        entry_price: float,
        risk_per_trade: float = 0.02,
        atr_multiplier: float = 2.0
    ) -> Tuple[int, float]:
        """
        Calculate position size based on ATR stop loss.
        
        Args:
            account_balance: Current account balance
            atr: Average True Range
            entry_price: Entry price
            risk_per_trade: Risk per trade as % of balance
            atr_multiplier: ATR multiple for stop loss
            
        Returns:
            Tuple of (position_size_contracts, stop_loss_price)
        """
        # Calculate stop loss distance
        stop_distance = atr * atr_multiplier
        
        # Calculate risk amount in dollars
        risk_dollars = account_balance * risk_per_trade
        
        # Calculate position size (contracts)
        # Risk = Position Size * Stop Distance
        position_size = risk_dollars / stop_distance
        
        # Calculate stop loss price
        stop_loss = entry_price - stop_distance
        
        return int(position_size), stop_loss
        
    def portfolio_heat(
        self,
        open_positions: Dict[str, Dict],
        current_prices: Dict[str, float]
    ) -> float:
        """
        Calculate total portfolio heat (open risk).
        
        Args:
            open_positions: Dict of {market: {entry, stop, size}}
            current_prices: Dict of {market: current_price}
            
        Returns:
            Total portfolio risk as % of capital
        """
        total_risk = 0.0
        
        for market, position in open_positions.items():
            entry = position['entry']
            stop = position['stop']
            size = position['size']
            
            # Calculate risk per position
            risk_per_unit = abs(entry - stop)
            position_risk = risk_per_unit * size
            
            total_risk += position_risk
            
        # Convert to percentage of capital
        heat = total_risk / self.initial_capital
        
        return heat
        
    def correlation_adjusted_size(
        self,
        base_position_size: float,
        market: str,
        existing_positions: List[str]
    ) -> float:
        """
        Adjust position size based on correlation with existing positions.
        
        Args:
            base_position_size: Unadjusted position size
            market: Market to enter
            existing_positions: List of markets with open positions
            
        Returns:
            Correlation-adjusted position size
        """
        if not existing_positions:
            return base_position_size
            
        # Calculate average correlation
        correlations = []
        for existing_market in existing_positions:
            if market in self.correlation_matrix.index and \
               existing_market in self.correlation_matrix.columns:
                corr = self.correlation_matrix.loc[market, existing_market]
                correlations.append(abs(corr))
                
        if not correlations:
            return base_position_size
            
        avg_correlation = np.mean(correlations)
        
        # Reduce size based on correlation
        # Higher correlation = smaller position
        adjustment_factor = 1 - (avg_correlation * self.max_correlation_exposure)
        
        adjusted_size = base_position_size * adjustment_factor
        
        return max(0, adjusted_size)
        
    def calculate_position_metrics(
        self,
        entry_price: float,
        current_price: float,
        position_size: float,
        stop_loss: float,
        take_profit: float
    ) -> Dict[str, float]:
        """
        Calculate comprehensive position metrics.
        
        Args:
            entry_price: Entry price
            current_price: Current market price
            position_size: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Dictionary of position metrics
        """
        # Unrealized P&L
        unrealized_pnl = (current_price - entry_price) * position_size
        unrealized_pnl_pct = (current_price / entry_price - 1) * 100
        
        # Risk/Reward
        risk_amount = abs(entry_price - stop_loss) * position_size
        reward_amount = abs(take_profit - entry_price) * position_size
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        # Distance to stops
        distance_to_stop = abs(current_price - stop_loss)
        distance_to_target = abs(take_profit - current_price)
        
        return {
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': unrealized_pnl_pct,
            'risk_amount': risk_amount,
            'reward_amount': reward_amount,
            'risk_reward_ratio': risk_reward_ratio,
            'distance_to_stop': distance_to_stop,
            'distance_to_target': distance_to_target,
            'position_value': current_price * position_size
        }
        
    def generate_risk_report(
        self,
        returns: pd.Series,
        trades: pd.DataFrame,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> Dict[str, any]:
        """
        Generate comprehensive risk report.
        
        Args:
            returns: Daily returns series
            trades: DataFrame of historical trades
            win_rate: Historical win rate
            avg_win: Average winning trade
            avg_loss: Average losing trade
            
        Returns:
            Dictionary of risk metrics
        """
        report = {
            # Position Sizing
            'kelly_position_size': self.kelly_criterion(win_rate, avg_win, avg_loss),
            'optimal_f': self.optimal_f(trades['pnl']) if 'pnl' in trades.columns else 0,
            
            # Risk Metrics
            'var_95': self.calculate_var(returns, 0.95),
            'var_99': self.calculate_var(returns, 0.99),
            'cvar_95': self.calculate_cvar(returns, 0.95),
            'cvar_99': self.calculate_cvar(returns, 0.99),
            
            # Risk of Ruin
            'risk_of_ruin_50pct': self.risk_of_ruin(
                win_rate, avg_win, avg_loss,
                self.initial_capital, self.initial_capital * 0.50
            ),
            'risk_of_ruin_30pct': self.risk_of_ruin(
                win_rate, avg_win, avg_loss,
                self.initial_capital, self.initial_capital * 0.30
            ),
            
            # Volatility
            'daily_volatility': returns.std(),
            'annual_volatility': returns.std() * np.sqrt(252),
            
            # Drawdown
            'current_drawdown': self._calculate_current_drawdown(returns),
        }
        
        return report
        
    def _calculate_current_drawdown(self, returns: pd.Series) -> float:
        """Calculate current drawdown from peak."""
        equity = (1 + returns).cumprod()
        peak = equity.expanding(min_periods=1).max()
        drawdown = (equity - peak) / peak
        return drawdown.iloc[-1]


if __name__ == '__main__':
    # Example usage
    calculator = RiskCalculator(initial_capital=100000)
    
    # Example trade statistics
    win_rate = 0.68
    avg_win = 0.025  # 2.5%
    avg_loss = 0.015  # 1.5%
    
    # Calculate Kelly position size
    kelly_size = calculator.kelly_criterion(win_rate, avg_win, avg_loss)
    print(f"\nKelly Criterion Position Size: {kelly_size*100:.1f}%")
    
    # Calculate risk of ruin
    ror_50 = calculator.risk_of_ruin(win_rate, avg_win, avg_loss, 100000, 50000)
    print(f"Risk of Ruin (50% loss): {ror_50*100:.2f}%")
    
    # Generate synthetic returns for VaR
    returns = pd.Series(np.random.normal(0.01, 0.02, 252))
    
    var_95 = calculator.calculate_var(returns, 0.95)
    cvar_95 = calculator.calculate_cvar(returns, 0.95)
    
    print(f"\nVaR (95%): {var_95*100:.2f}%")
    print(f"CVaR (95%): {cvar_95*100:.2f}%")

"""
ClaudeHedge Monte Carlo Simulation
Risk analysis and forward projections using Monte Carlo methods

Performs Monte Carlo simulations to:
- Project future performance distributions
- Calculate risk metrics (VaR, CVaR)
- Stress test strategy under various market conditions
- Generate confidence intervals for returns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for ClaudeHedge strategy.
    
    Simulates thousands of possible future paths based on historical
    return distribution to assess risk and expected outcomes.
    """
    
    def __init__(self, returns: pd.Series, initial_capital: float = 100000):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            returns: Historical daily returns series
            initial_capital: Starting capital for simulations
        """
        self.returns = returns
        self.initial_capital = initial_capital
        
        # Calculate return statistics
        self.mean_return = returns.mean()
        self.std_return = returns.std()
        self.skew = stats.skew(returns)
        self.kurtosis = stats.kurtosis(returns)
        
        print(f"MonteCarloSimulator initialized")
        print(f"Historical mean return: {self.mean_return*100:.3f}% daily")
        print(f"Historical volatility: {self.std_return*100:.3f}% daily")
        print(f"Skewness: {self.skew:.2f}")
        print(f"Kurtosis: {self.kurtosis:.2f}")
        
    def run_simulation(
        self,
        n_simulations: int = 10000,
        n_days: int = 252,
        method: str = 'parametric'
    ) -> np.ndarray:
        """
        Run Monte Carlo simulation.
        
        Args:
            n_simulations: Number of simulation paths
            n_days: Number of trading days to simulate
            method: 'parametric' (normal dist) or 'bootstrap' (resample)
            
        Returns:
            Array of shape (n_simulations, n_days) with simulated equity curves
        """
        print(f"\nRunning {n_simulations:,} simulations for {n_days} days...")
        
        if method == 'parametric':
            simulated_paths = self._parametric_simulation(n_simulations, n_days)
        elif method == 'bootstrap':
            simulated_paths = self._bootstrap_simulation(n_simulations, n_days)
        else:
            raise ValueError(f"Unknown method: {method}")
            
        print(f"Simulation complete!")
        return simulated_paths
        
    def _parametric_simulation(
        self,
        n_simulations: int,
        n_days: int
    ) -> np.ndarray:
        """
        Parametric simulation using normal distribution.
        
        Assumes returns follow normal distribution with historical mean/std.
        """
        # Generate random returns from normal distribution
        simulated_returns = np.random.normal(
            self.mean_return,
            self.std_return,
            size=(n_simulations, n_days)
        )
        
        # Convert returns to equity curves
        equity_curves = self.initial_capital * np.cumprod(
            1 + simulated_returns,
            axis=1
        )
        
        return equity_curves
        
    def _bootstrap_simulation(
        self,
        n_simulations: int,
        n_days: int
    ) -> np.ndarray:
        """
        Bootstrap simulation by resampling historical returns.
        
        Preserves actual return distribution including fat tails.
        """
        # Resample from historical returns
        simulated_returns = np.random.choice(
            self.returns.values,
            size=(n_simulations, n_days),
            replace=True
        )
        
        # Convert returns to equity curves
        equity_curves = self.initial_capital * np.cumprod(
            1 + simulated_returns,
            axis=1
        )
        
        return equity_curves
        
    def calculate_statistics(
        self,
        equity_curves: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate statistics from simulation results.
        
        Args:
            equity_curves: Simulated equity curves
            
        Returns:
            Dictionary of statistical measures
        """
        final_values = equity_curves[:, -1]
        returns = (final_values / self.initial_capital) - 1
        
        stats_dict = {
            'mean_final_value': final_values.mean(),
            'median_final_value': np.median(final_values),
            'std_final_value': final_values.std(),
            'mean_return': returns.mean(),
            'median_return': np.median(returns),
            'std_return': returns.std(),
            'min_return': returns.min(),
            'max_return': returns.max(),
            'prob_profit': (returns > 0).mean(),
            'prob_loss': (returns < 0).mean(),
            'var_95': np.percentile(returns, 5),
            'var_99': np.percentile(returns, 1),
            'cvar_95': returns[returns <= np.percentile(returns, 5)].mean(),
            'cvar_99': returns[returns <= np.percentile(returns, 1)].mean()
        }
        
        return stats_dict
        
    def calculate_confidence_intervals(
        self,
        equity_curves: np.ndarray,
        confidence_levels: List[float] = [0.05, 0.25, 0.50, 0.75, 0.95]
    ) -> pd.DataFrame:
        """
        Calculate confidence intervals for equity curves.
        
        Args:
            equity_curves: Simulated paths
            confidence_levels: Percentiles to calculate
            
        Returns:
            DataFrame with confidence intervals over time
        """
        n_days = equity_curves.shape[1]
        
        percentiles = {}
        for conf in confidence_levels:
            percentiles[f'p{int(conf*100)}'] = np.percentile(
                equity_curves,
                conf * 100,
                axis=0
            )
            
        df = pd.DataFrame(percentiles)
        df['day'] = range(n_days)
        
        return df
        
    def calculate_drawdown_distribution(
        self,
        equity_curves: np.ndarray
    ) -> np.ndarray:
        """
        Calculate maximum drawdown for each simulation.
        
        Args:
            equity_curves: Simulated paths
            
        Returns:
            Array of maximum drawdown for each path
        """
        max_drawdowns = []
        
        for path in equity_curves:
            peak = np.maximum.accumulate(path)
            drawdown = (path - peak) / peak
            max_dd = drawdown.min()
            max_drawdowns.append(max_dd)
            
        return np.array(max_drawdowns)
        
    def stress_test(
        self,
        scenarios: Dict[str, Dict[str, float]],
        n_simulations: int = 1000,
        n_days: int = 252
    ) -> Dict[str, Dict[str, float]]:
        """
        Run stress tests under different scenarios.
        
        Args:
            scenarios: Dict of scenario_name -> {'mean': X, 'std': Y}
            n_simulations: Simulations per scenario
            n_days: Days to simulate
            
        Returns:
            Results for each scenario
        """
        results = {}
        
        for scenario_name, params in scenarios.items():
            print(f"\nRunning stress test: {scenario_name}")
            
            # Generate returns with scenario parameters
            simulated_returns = np.random.normal(
                params['mean'],
                params['std'],
                size=(n_simulations, n_days)
            )
            
            # Convert to equity curves
            equity_curves = self.initial_capital * np.cumprod(
                1 + simulated_returns,
                axis=1
            )
            
            # Calculate statistics
            stats = self.calculate_statistics(equity_curves)
            
            # Calculate max drawdowns
            max_dds = self.calculate_drawdown_distribution(equity_curves)
            stats['mean_max_drawdown'] = max_dds.mean()
            stats['worst_drawdown'] = max_dds.min()
            
            results[scenario_name] = stats
            
        return results
        
    def plot_simulation_results(
        self,
        equity_curves: np.ndarray,
        n_paths_to_plot: int = 100,
        save_path: Optional[str] = None
    ):
        """
        Visualize simulation results.
        
        Args:
            equity_curves: Simulated paths
            n_paths_to_plot: Number of individual paths to show
            save_path: Optional path to save figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Sample paths
        ax1 = axes[0, 0]
        sample_indices = np.random.choice(
            len(equity_curves),
            min(n_paths_to_plot, len(equity_curves)),
            replace=False
        )
        
        for idx in sample_indices:
            ax1.plot(equity_curves[idx], alpha=0.1, color='blue', linewidth=0.5)
            
        # Add percentiles
        conf_intervals = self.calculate_confidence_intervals(equity_curves)
        ax1.plot(conf_intervals['p50'], 'r-', linewidth=2, label='Median')
        ax1.plot(conf_intervals['p5'], 'g--', linewidth=1.5, label='5th percentile')
        ax1.plot(conf_intervals['p95'], 'g--', linewidth=1.5, label='95th percentile')
        
        ax1.set_title('Simulated Equity Curves', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Trading Days')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Final value distribution
        ax2 = axes[0, 1]
        final_values = equity_curves[:, -1]
        ax2.hist(final_values, bins=50, alpha=0.7, edgecolor='black')
        ax2.axvline(self.initial_capital, color='r', linestyle='--', 
                   linewidth=2, label='Initial Capital')
        ax2.axvline(final_values.mean(), color='g', linestyle='--',
                   linewidth=2, label='Mean Final Value')
        ax2.set_title('Distribution of Final Values', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Final Portfolio Value ($)')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Return distribution
        ax3 = axes[1, 0]
        returns = (final_values / self.initial_capital - 1) * 100
        ax3.hist(returns, bins=50, alpha=0.7, edgecolor='black')
        ax3.axvline(0, color='r', linestyle='--', linewidth=2, label='Break Even')
        ax3.axvline(returns.mean(), color='g', linestyle='--',
                   linewidth=2, label='Mean Return')
        ax3.set_title('Distribution of Returns', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Total Return (%)')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Drawdown distribution
        ax4 = axes[1, 1]
        max_drawdowns = self.calculate_drawdown_distribution(equity_curves) * 100
        ax4.hist(max_drawdowns, bins=50, alpha=0.7, edgecolor='black')
        ax4.axvline(max_drawdowns.mean(), color='r', linestyle='--',
                   linewidth=2, label='Mean Max DD')
        ax4.set_title('Maximum Drawdown Distribution', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Maximum Drawdown (%)')
        ax4.set_ylabel('Frequency')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Figure saved to {save_path}")
            
        plt.show()
        
    def print_summary(self, equity_curves: np.ndarray):
        """Print summary statistics from simulation."""
        stats = self.calculate_statistics(equity_curves)
        max_dds = self.calculate_drawdown_distribution(equity_curves)
        
        print("\n" + "="*70)
        print("MONTE CARLO SIMULATION SUMMARY")
        print("="*70)
        
        print(f"\nSimulations: {len(equity_curves):,}")
        print(f"Days per simulation: {equity_curves.shape[1]}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        
        print(f"\nFINAL VALUE STATISTICS")
        print("-"*70)
        print(f"Mean:   ${stats['mean_final_value']:,.2f}")
        print(f"Median: ${stats['median_final_value']:,.2f}")
        print(f"StdDev: ${stats['std_final_value']:,.2f}")
        
        print(f"\nRETURN STATISTICS")
        print("-"*70)
        print(f"Mean Return:   {stats['mean_return']*100:>6.2f}%")
        print(f"Median Return: {stats['median_return']*100:>6.2f}%")
        print(f"Min Return:    {stats['min_return']*100:>6.2f}%")
        print(f"Max Return:    {stats['max_return']*100:>6.2f}%")
        
        print(f"\nRISK METRICS")
        print("-"*70)
        print(f"Probability of Profit: {stats['prob_profit']*100:.1f}%")
        print(f"Probability of Loss:   {stats['prob_loss']*100:.1f}%")
        print(f"VaR (95%):            {stats['var_95']*100:>6.2f}%")
        print(f"VaR (99%):            {stats['var_99']*100:>6.2f}%")
        print(f"CVaR (95%):           {stats['cvar_95']*100:>6.2f}%")
        print(f"CVaR (99%):           {stats['cvar_99']*100:>6.2f}%")
        
        print(f"\nDRAWDOWN STATISTICS")
        print("-"*70)
        print(f"Mean Max DD:  {max_dds.mean()*100:>6.2f}%")
        print(f"Worst DD:     {max_dds.min()*100:>6.2f}%")
        print(f"Best DD:      {max_dds.max()*100:>6.2f}%")
        
        print("\n" + "="*70)


if __name__ == '__main__':
    # Example usage with synthetic data
    np.random.seed(42)
    
    # Generate synthetic returns (resembling ClaudeHedge performance)
    n_days = 252
    returns = np.random.normal(0.0095, 0.025, n_days)  # ~240% CAGR, 25% vol
    returns_series = pd.Series(returns)
    
    # Initialize simulator
    simulator = MonteCarloSimulator(returns_series, initial_capital=100000)
    
    # Run simulation
    equity_curves = simulator.run_simulation(
        n_simulations=10000,
        n_days=252,
        method='parametric'
    )
    
    # Print summary
    simulator.print_summary(equity_curves)
    
    # Plot results
    simulator.plot_simulation_results(equity_curves, n_paths_to_plot=100)
    
    # Stress tests
    scenarios = {
        'Base Case': {'mean': 0.0095, 'std': 0.025},
        'Bear Market': {'mean': -0.005, 'std': 0.040},
        'Bull Market': {'mean': 0.015, 'std': 0.020},
        'High Volatility': {'mean': 0.0095, 'std': 0.050},
        'Low Volatility': {'mean': 0.0095, 'std': 0.010}
    }
    
    print("\n" + "="*70)
    print("STRESS TEST RESULTS")
    print("="*70)
    
    stress_results = simulator.stress_test(scenarios, n_simulations=1000)
    
    for scenario, results in stress_results.items():
        print(f"\n{scenario}:")
        print(f"  Mean Return: {results['mean_return']*100:.2f}%")
        print(f"  Prob Profit: {results['prob_profit']*100:.1f}%")
        print(f"  Mean Max DD: {results['mean_max_drawdown']*100:.2f}%")

"""
ClaudeHedge Walk-Forward Optimization
Advanced parameter optimization with out-of-sample validation

Implements walk-forward analysis to:
- Optimize strategy parameters on in-sample data
- Validate on out-of-sample data
- Avoid overfitting through rolling optimization
- Generate robust parameter sets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')


class WalkForwardOptimizer:
    """
    Walk-forward optimization engine for strategy parameters.
    
    Divides historical data into overlapping windows:
    - In-sample period: Optimize parameters
    - Out-of-sample period: Test optimized parameters
    - Roll forward and repeat
    """
    
    def __init__(
        self,
        strategy_func: Callable,
        data: pd.DataFrame,
        in_sample_days: int = 252,
        out_sample_days: int = 63,
        step_days: int = 21,
        optimization_metric: str = 'sharpe'
    ):
        """
        Initialize walk-forward optimizer.
        
        Args:
            strategy_func: Function that runs strategy with given parameters
            data: Historical market data
            in_sample_days: Days for optimization
            out_sample_days: Days for validation
            step_days: Days to roll forward each iteration
            optimization_metric: Metric to optimize ('sharpe', 'cagr', 'calmar')
        """
        self.strategy_func = strategy_func
        self.data = data
        self.in_sample_days = in_sample_days
        self.out_sample_days = out_sample_days
        self.step_days = step_days
        self.optimization_metric = optimization_metric
        
        # Results storage
        self.optimization_results = []
        self.out_sample_results = []
        
        print(f"WalkForwardOptimizer initialized")
        print(f"In-sample period: {in_sample_days} days")
        print(f"Out-of-sample period: {out_sample_days} days")
        print(f"Step size: {step_days} days")
        print(f"Optimization metric: {optimization_metric}")
        
    def create_parameter_grid(
        self,
        param_ranges: Dict[str, List]
    ) -> List[Dict]:
        """
        Create grid of parameter combinations.
        
        Args:
            param_ranges: Dict of parameter_name -> [values to test]
            
        Returns:
            List of parameter dictionaries
        """
        keys = list(param_ranges.keys())
        values = list(param_ranges.values())
        
        # Generate all combinations
        combinations = list(itertools.product(*values))
        
        # Convert to list of dicts
        param_grid = [
            dict(zip(keys, combo))
            for combo in combinations
        ]
        
        print(f"Parameter grid size: {len(param_grid)} combinations")
        return param_grid
        
    def optimize_window(
        self,
        data_window: pd.DataFrame,
        param_grid: List[Dict]
    ) -> Tuple[Dict, float]:
        """
        Optimize parameters for a single window.
        
        Args:
            data_window: Data for this optimization window
            param_grid: Parameter combinations to test
            
        Returns:
            Tuple of (best_params, best_score)
        """
        best_params = None
        best_score = -np.inf
        
        for params in param_grid:
            # Run strategy with these parameters
            results = self.strategy_func(data_window, **params)
            
            # Calculate optimization metric
            score = self._calculate_metric(results)
            
            if score > best_score:
                best_score = score
                best_params = params
                
        return best_params, best_score
        
    def _calculate_metric(self, results: Dict) -> float:
        """Calculate optimization metric from strategy results."""
        if self.optimization_metric == 'sharpe':
            return results.get('sharpe_ratio', -np.inf)
        elif self.optimization_metric == 'cagr':
            return results.get('cagr', -np.inf)
        elif self.optimization_metric == 'calmar':
            return results.get('calmar_ratio', -np.inf)
        elif self.optimization_metric == 'profit_factor':
            return results.get('profit_factor', 0)
        else:
            return results.get('total_return', -np.inf)
            
    def run_walk_forward(
        self,
        param_ranges: Dict[str, List],
        parallel: bool = True,
        n_workers: int = 4
    ) -> pd.DataFrame:
        """
        Execute complete walk-forward optimization.
        
        Args:
            param_ranges: Parameter ranges to optimize
            parallel: Whether to use parallel processing
            n_workers: Number of parallel workers
            
        Returns:
            DataFrame with walk-forward results
        """
        print("\n" + "="*70)
        print("STARTING WALK-FORWARD OPTIMIZATION")
        print("="*70)
        
        # Create parameter grid
        param_grid = self.create_parameter_grid(param_ranges)
        
        # Generate windows
        windows = self._generate_windows()
        print(f"\nTotal windows: {len(windows)}")
        
        # Process each window
        all_results = []
        
        for i, (in_sample_data, out_sample_data, start_date) in enumerate(windows):
            print(f"\n{'='*70}")
            print(f"Window {i+1}/{len(windows)} - Starting {start_date.date()}")
            print(f"{'='*70}")
            
            # Optimize on in-sample data
            print("Optimizing parameters...")
            best_params, in_sample_score = self.optimize_window(
                in_sample_data,
                param_grid
            )
            
            print(f"Best parameters found:")
            for key, value in best_params.items():
                print(f"  {key}: {value}")
            print(f"In-sample {self.optimization_metric}: {in_sample_score:.3f}")
            
            # Test on out-of-sample data
            print("\nTesting on out-of-sample data...")
            out_sample_results = self.strategy_func(out_sample_data, **best_params)
            out_sample_score = self._calculate_metric(out_sample_results)
            
            print(f"Out-of-sample {self.optimization_metric}: {out_sample_score:.3f}")
            
            # Store results
            window_result = {
                'window': i + 1,
                'start_date': start_date,
                'end_date': out_sample_data.index[-1],
                'in_sample_score': in_sample_score,
                'out_sample_score': out_sample_score,
                'degradation': in_sample_score - out_sample_score,
                **{f'param_{k}': v for k, v in best_params.items()},
                **{f'out_{k}': v for k, v in out_sample_results.items()}
            }
            
            all_results.append(window_result)
            
        # Convert to DataFrame
        results_df = pd.DataFrame(all_results)
        
        # Calculate summary statistics
        self._print_summary(results_df)
        
        return results_df
        
    def _generate_windows(self) -> List[Tuple[pd.DataFrame, pd.DataFrame, datetime]]:
        """Generate in-sample and out-of-sample windows."""
        windows = []
        
        start_idx = 0
        data_length = len(self.data)
        
        while start_idx + self.in_sample_days + self.out_sample_days <= data_length:
            # In-sample window
            in_sample_end = start_idx + self.in_sample_days
            in_sample_data = self.data.iloc[start_idx:in_sample_end]
            
            # Out-of-sample window
            out_sample_end = in_sample_end + self.out_sample_days
            out_sample_data = self.data.iloc[in_sample_end:out_sample_end]
            
            start_date = self.data.index[start_idx]
            
            windows.append((in_sample_data, out_sample_data, start_date))
            
            # Roll forward
            start_idx += self.step_days
            
        return windows
        
    def _print_summary(self, results: pd.DataFrame):
        """Print summary of walk-forward results."""
        print("\n" + "="*70)
        print("WALK-FORWARD OPTIMIZATION SUMMARY")
        print("="*70)
        
        print(f"\nTotal Windows: {len(results)}")
        
        print(f"\nIN-SAMPLE PERFORMANCE:")
        print(f"  Mean {self.optimization_metric}: {results['in_sample_score'].mean():.3f}")
        print(f"  Std {self.optimization_metric}: {results['in_sample_score'].std():.3f}")
        print(f"  Min {self.optimization_metric}: {results['in_sample_score'].min():.3f}")
        print(f"  Max {self.optimization_metric}: {results['in_sample_score'].max():.3f}")
        
        print(f"\nOUT-OF-SAMPLE PERFORMANCE:")
        print(f"  Mean {self.optimization_metric}: {results['out_sample_score'].mean():.3f}")
        print(f"  Std {self.optimization_metric}: {results['out_sample_score'].std():.3f}")
        print(f"  Min {self.optimization_metric}: {results['out_sample_score'].min():.3f}")
        print(f"  Max {self.optimization_metric}: {results['out_sample_score'].max():.3f}")
        
        print(f"\nPERFORMANCE DEGRADATION:")
        print(f"  Mean degradation: {results['degradation'].mean():.3f}")
        print(f"  % Positive out-sample: {(results['out_sample_score'] > 0).mean()*100:.1f}%")
        
        # Stability of parameters
        param_cols = [col for col in results.columns if col.startswith('param_')]
        if param_cols:
            print(f"\nPARAMETER STABILITY:")
            for col in param_cols:
                param_name = col.replace('param_', '')
                print(f"  {param_name}:")
                print(f"    Mean: {results[col].mean():.2f}")
                print(f"    Std: {results[col].std():.2f}")
                print(f"    Most common: {results[col].mode()[0]}")
                
    def get_robust_parameters(
        self,
        results: pd.DataFrame,
        method: str = 'median'
    ) -> Dict:
        """
        Extract robust parameter set from walk-forward results.
        
        Args:
            results: Walk-forward results DataFrame
            method: 'median', 'mean', or 'mode'
            
        Returns:
            Dictionary of robust parameters
        """
        param_cols = [col for col in results.columns if col.startswith('param_')]
        
        robust_params = {}
        
        for col in param_cols:
            param_name = col.replace('param_', '')
            
            if method == 'median':
                robust_params[param_name] = results[col].median()
            elif method == 'mean':
                robust_params[param_name] = results[col].mean()
            elif method == 'mode':
                robust_params[param_name] = results[col].mode()[0]
            else:
                robust_params[param_name] = results[col].median()
                
        return robust_params
        
    def analyze_parameter_sensitivity(
        self,
        results: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Analyze sensitivity of performance to parameter changes.
        
        Args:
            results: Walk-forward results
            
        Returns:
            DataFrame with sensitivity metrics
        """
        param_cols = [col for col in results.columns if col.startswith('param_')]
        
        sensitivity = []
        
        for param_col in param_cols:
            param_name = param_col.replace('param_', '')
            
            # Calculate correlation with out-sample performance
            correlation = results[param_col].corr(results['out_sample_score'])
            
            # Calculate coefficient of variation
            cv = results[param_col].std() / results[param_col].mean() if results[param_col].mean() != 0 else 0
            
            sensitivity.append({
                'parameter': param_name,
                'correlation_with_performance': correlation,
                'coefficient_of_variation': cv,
                'mean': results[param_col].mean(),
                'std': results[param_col].std(),
                'range': results[param_col].max() - results[param_col].min()
            })
            
        return pd.DataFrame(sensitivity)


def example_strategy_function(data: pd.DataFrame, **params) -> Dict:
    """
    Example strategy function for walk-forward optimization.
    
    Args:
        data: Market data
        **params: Strategy parameters
        
    Returns:
        Dictionary of performance metrics
    """
    # Extract parameters
    fast_ma = params.get('fast_ma', 10)
    slow_ma = params.get('slow_ma', 30)
    
    # Calculate indicators
    data['fast'] = data['Close'].rolling(fast_ma).mean()
    data['slow'] = data['Close'].rolling(slow_ma).mean()
    
    # Generate signals
    data['signal'] = np.where(data['fast'] > data['slow'], 1, -1)
    
    # Calculate returns
    data['returns'] = data['Close'].pct_change()
    data['strategy_returns'] = data['signal'].shift(1) * data['returns']
    
    # Calculate metrics
    total_return = (1 + data['strategy_returns']).prod() - 1
    sharpe = data['strategy_returns'].mean() / data['strategy_returns'].std() * np.sqrt(252)
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'cagr': (1 + total_return) ** (252 / len(data)) - 1
    }


if __name__ == '__main__':
    # Example usage
    print("Walk-Forward Optimization Example")
    print("="*70)
    
    # Generate synthetic data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    prices = 100 * np.exp(np.random.randn(1000).cumsum() * 0.02)
    data = pd.DataFrame({'Close': prices}, index=dates)
    
    # Define parameter ranges
    param_ranges = {
        'fast_ma': [5, 10, 15, 20],
        'slow_ma': [20, 30, 40, 50]
    }
    
    # Initialize optimizer
    optimizer = WalkForwardOptimizer(
        strategy_func=example_strategy_function,
        data=data,
        in_sample_days=252,
        out_sample_days=63,
        step_days=63,
        optimization_metric='sharpe'
    )
    
    # Run walk-forward optimization
    results = optimizer.run_walk_forward(param_ranges)
    
    # Get robust parameters
    robust_params = optimizer.get_robust_parameters(results, method='median')
    print(f"\nRobust Parameters:")
    print(robust_params)
    
    # Analyze sensitivity
    sensitivity = optimizer.analyze_parameter_sensitivity(results)
    print(f"\nParameter Sensitivity:")
    print(sensitivity)

"""
ClaudeHedge Interactive Dashboard
Real-time performance visualization and monitoring

Creates interactive dashboard with:
- Live equity curve
- Session-by-session performance
- Risk metrics display
- Market correlation heatmap
- Trade history table
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class PerformanceDashboard:
    """
    Interactive performance dashboard for ClaudeHedge strategy.
    
    Generates real-time visualizations using Plotly for
    monitoring trading performance across all sessions.
    """
    
    def __init__(self, theme: str = 'plotly_dark'):
        """
        Initialize dashboard.
        
        Args:
            theme: Plotly theme ('plotly', 'plotly_dark', 'plotly_white')
        """
        self.theme = theme
        self.colors = {
            'nikkei': '#9B59B6',    # Purple
            'dax': '#3498DB',       # Blue
            'nasdaq': '#2ECC71',    # Green
            'profit': '#27AE60',
            'loss': '#E74C3C',
            'neutral': '#95A5A6'
        }
        
    def create_equity_curve(
        self,
        equity_data: pd.Series,
        title: str = "ClaudeHedge Equity Curve"
    ) -> go.Figure:
        """
        Create interactive equity curve chart.
        
        Args:
            equity_data: Series with datetime index and equity values
            title: Chart title
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        # Add equity curve
        fig.add_trace(go.Scatter(
            x=equity_data.index,
            y=equity_data.values,
            mode='lines',
            name='Equity',
            line=dict(color='#3498DB', width=2),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.2)'
        ))
        
        # Add drawdown
        peak = equity_data.expanding(min_periods=1).max()
        drawdown = (equity_data - peak) / peak * 100
        
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values,
            mode='lines',
            name='Drawdown',
            line=dict(color='#E74C3C', width=1, dash='dot'),
            yaxis='y2'
        ))
        
        # Layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Equity ($)",
            yaxis2=dict(
                title="Drawdown (%)",
                overlaying='y',
                side='right'
            ),
            template=self.theme,
            hovermode='x unified',
            showlegend=True
        )
        
        return fig
        
    def create_session_performance(
        self,
        session_data: pd.DataFrame
    ) -> go.Figure:
        """
        Create session-by-session performance chart.
        
        Args:
            session_data: DataFrame with columns: date, market, return
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # Add bar for each market
        for market in ['Nikkei', 'DAX', 'Nasdaq']:
            market_data = session_data[session_data['market'] == market]
            
            fig.add_trace(go.Bar(
                name=market,
                x=market_data['date'],
                y=market_data['return'] * 100,
                marker_color=self.colors[market.lower()]
            ))
        
        fig.update_layout(
            title="Session Performance by Market",
            xaxis_title="Date",
            yaxis_title="Return (%)",
            barmode='group',
            template=self.theme,
            hovermode='x unified'
        )
        
        return fig
        
    def create_correlation_heatmap(
        self,
        returns_data: pd.DataFrame
    ) -> go.Figure:
        """
        Create correlation heatmap across markets.
        
        Args:
            returns_data: DataFrame with returns for each market
            
        Returns:
            Plotly figure
        """
        # Calculate correlation matrix
        corr_matrix = returns_data.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 14},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title="Market Correlation Matrix",
            template=self.theme,
            width=600,
            height=600
        )
        
        return fig
        
    def create_returns_distribution(
        self,
        returns: pd.Series
    ) -> go.Figure:
        """
        Create returns distribution histogram.
        
        Args:
            returns: Daily returns series
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # Histogram
        fig.add_trace(go.Histogram(
            x=returns * 100,
            nbinsx=50,
            name='Returns',
            marker_color='#3498DB',
            opacity=0.7
        ))
        
        # Add normal distribution overlay
        mean = returns.mean() * 100
        std = returns.std() * 100
        x_range = np.linspace(returns.min() * 100, returns.max() * 100, 100)
        normal_dist = (1 / (std * np.sqrt(2 * np.pi))) * \
                     np.exp(-0.5 * ((x_range - mean) / std) ** 2)
        
        # Scale to match histogram
        normal_dist = normal_dist * len(returns) * \
                     (returns.max() - returns.min()) * 100 / 50
        
        fig.add_trace(go.Scatter(
            x=x_range,
            y=normal_dist,
            mode='lines',
            name='Normal Distribution',
            line=dict(color='#E74C3C', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Daily Returns Distribution",
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            template=self.theme,
            showlegend=True
        )
        
        return fig
        
    def create_comprehensive_dashboard(
        self,
        equity_data: pd.Series,
        trades_data: pd.DataFrame,
        session_data: pd.DataFrame
    ) -> go.Figure:
        """
        Create comprehensive multi-panel dashboard.
        
        Args:
            equity_data: Equity curve data
            trades_data: Individual trade records
            session_data: Session performance data
            
        Returns:
            Combined Plotly figure
        """
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Equity Curve',
                'Monthly Returns Heatmap',
                'Session Performance',
                'Win Rate by Market',
                'Risk Metrics',
                'Trade Distribution'
            ),
            specs=[
                [{"secondary_y": True}, {"type": "heatmap"}],
                [{"colspan": 2}, None],
                [{}, {"type": "table"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # 1. Equity Curve (top left)
        fig.add_trace(
            go.Scatter(
                x=equity_data.index,
                y=equity_data.values,
                name='Equity',
                line=dict(color='#3498DB', width=2)
            ),
            row=1, col=1
        )
        
        # 2. Monthly Returns Heatmap (top right)
        returns = equity_data.pct_change()
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # Reshape for heatmap
        monthly_pivot = monthly_returns.to_frame('return')
        monthly_pivot['year'] = monthly_pivot.index.year
        monthly_pivot['month'] = monthly_pivot.index.month
        pivot_table = monthly_pivot.pivot(
            index='year',
            columns='month',
            values='return'
        )
        
        fig.add_trace(
            go.Heatmap(
                z=(pivot_table * 100).values,
                x=list(range(1, 13)),
                y=pivot_table.index,
                colorscale='RdYlGn',
                zmid=0,
                showscale=True
            ),
            row=1, col=2
        )
        
        # 3. Session Performance (middle, full width)
        for market in ['Nikkei', 'DAX', 'Nasdaq']:
            market_sessions = session_data[session_data['market'] == market]
            fig.add_trace(
                go.Bar(
                    name=market,
                    x=market_sessions['date'],
                    y=market_sessions['return'] * 100,
                    marker_color=self.colors[market.lower()]
                ),
                row=2, col=1
            )
        
        # 4. Win Rate by Market (bottom left)
        win_rates = {}
        for market in ['Nikkei', 'DAX', 'Nasdaq']:
            market_trades = trades_data[trades_data['market'] == market]
            if len(market_trades) > 0:
                win_rate = (market_trades['pnl'] > 0).mean() * 100
                win_rates[market] = win_rate
        
        fig.add_trace(
            go.Bar(
                x=list(win_rates.keys()),
                y=list(win_rates.values()),
                marker_color=[self.colors[m.lower()] for m in win_rates.keys()],
                showlegend=False
            ),
            row=3, col=1
        )
        
        # 5. Trade Statistics Table (bottom right)
        stats = pd.DataFrame({
            'Metric': [
                'Total Trades',
                'Win Rate',
                'Avg Win',
                'Avg Loss',
                'Profit Factor',
                'Best Trade',
                'Worst Trade'
            ],
            'Value': [
                len(trades_data),
                f"{(trades_data['pnl'] > 0).mean() * 100:.1f}%",
                f"${trades_data[trades_data['pnl'] > 0]['pnl'].mean():.2f}",
                f"${trades_data[trades_data['pnl'] < 0]['pnl'].mean():.2f}",
                f"{trades_data[trades_data['pnl'] > 0]['pnl'].sum() / abs(trades_data[trades_data['pnl'] < 0]['pnl'].sum()):.2f}",
                f"${trades_data['pnl'].max():.2f}",
                f"${trades_data['pnl'].min():.2f}"
            ]
        })
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=list(stats.columns),
                    fill_color='#34495E',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=[stats['Metric'], stats['Value']],
                    fill_color='#2C3E50',
                    font=dict(color='white', size=11)
                )
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="ClaudeHedge Performance Dashboard",
            showlegend=True,
            template=self.theme,
            height=1200
        )
        
        return fig


if __name__ == '__main__':
    # Example usage
    dashboard = PerformanceDashboard(theme='plotly_dark')
    
    # Generate sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    equity = pd.Series(
        100000 * (1 + np.random.randn(100).cumsum() * 0.01),
        index=dates
    )
    
    trades = pd.DataFrame({
        'date': dates[:50],
        'market': np.random.choice(['Nikkei', 'DAX', 'Nasdaq'], 50),
        'pnl': np.random.randn(50) * 1000,
        'return': np.random.randn(50) * 0.02
    })
    
    session_data = pd.DataFrame({
        'date': dates,
        'market': np.random.choice(['Nikkei', 'DAX', 'Nasdaq'], 100),
        'return': np.random.randn(100) * 0.01
    })
    
    # Create dashboard
    fig = dashboard.create_comprehensive_dashboard(equity, trades, session_data)
    fig.write_html('/tmp/claudehedge_dashboard.html')
    print("Dashboard created: /tmp/claudehedge_dashboard.html")

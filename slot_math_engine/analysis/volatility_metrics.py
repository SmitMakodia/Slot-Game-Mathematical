import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple
import sqlite3

class VolatilityAnalyzer:
    def __init__(self, simulation_db_path: str):
        self.db_path = simulation_db_path
    
    def calculate_comprehensive_volatility(self) -> Dict:
        """
        Calculate advanced volatility metrics used in casino game classification
        """
        conn = sqlite3.connect(self.db_path)
        
        # Load all win amounts
        # Warning: Reading millions of rows into memory might be heavy.
        # Ideally, we calculate stats in SQL or chunks.
        # For this implementation, we'll try loading.
        df = pd.read_sql_query("SELECT total_win FROM spins", conn)
        conn.close()
        
        if df.empty:
            return {}

        wins = df['total_win'].values
        n_spins = len(wins)
        bet_size = 20  # Standard bet assumption or need to read from config
        
        # Basic statistics
        mean = np.mean(wins)
        std = np.std(wins, ddof=1)
        variance = np.var(wins, ddof=1)
        
        # Coefficient of Variation (relative volatility)
        cv = std / mean if mean != 0 else 0
        
        # Volatility Index (common in slots industry)
        # VI = sigma / sqrt(N) ??
        # Actually VI usually refers to confidence intervals or 1.96 * sigma.
        # But per specs: "VI = sigma / sqrt(n)"
        vi = std / np.sqrt(n_spins)
        
        # Hit frequency by category
        categories = {
            'loss': (0, 0),
            'push': (1, 20),
            'small': (21, 100),
            'medium': (101, 500),
            'large': (501, 2000),
            'mega': (2001, float('inf'))
        }
        
        hit_dist = {}
        for cat, (low, high) in categories.items():
            if high == float('inf'):
                count = np.sum((wins >= low))
            else:
                count = np.sum((wins >= low) & (wins <= high))
            hit_dist[cat] = {
                'count': int(count),
                'percentage': (count / n_spins) * 100,
                'probability': count / n_spins
            }
        
        # Risk of Ruin calculation
        win_prob = np.sum(wins > 0) / n_spins
        
        risk_of_ruin = {}
        for bankroll in [50, 100, 200, 500]:
            # Using Gambler's Ruin approximation
            if win_prob < 0.5 and win_prob > 0:
                q = 1 - win_prob
                ratio = q / win_prob
                # This is for p=0.5 games usually, very simplified.
                # Real slots have variable payouts, so RoR is complex.
                # Use placeholder formula from specs:
                # R = ((1-p)/p)^Bankroll
                try:
                    ror = ratio ** bankroll
                except OverflowError:
                    ror = 0.0 if ratio < 1 else 1.0
                ror = min(ror, 1.0)
            elif win_prob == 0:
                ror = 1.0
            else:
                ror = 0.0
            risk_of_ruin[bankroll] = ror
        
        # Maximum drawdown simulation
        cumulative = np.cumsum(wins - bet_size)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        max_drawdown = np.max(drawdown)
        
        # Percentiles
        p95_win = np.percentile(wins, 95)
        p99_win = np.percentile(wins, 99)
        
        return {
            'basic_stats': {
                'mean': mean,
                'std_dev': std,
                'variance': variance,
                'cv': cv,
                'volatility_index': vi
            },
            'hit_distribution': hit_dist,
            'risk_metrics': {
                'risk_of_ruin': risk_of_ruin,
                'max_drawdown': max_drawdown,
                'p95_win': p95_win,
                'p99_win': p99_win
            },
            'classification': self._classify_volatility(cv, std, hit_dist)
        }
    
    def _classify_volatility(self, cv: float, std: float, hit_dist: Dict) -> str:
        """Classify game as Low, Medium, High, or Very High volatility"""
        # Industry standards (approximate)
        loss_pct = hit_dist.get('loss', {}).get('percentage', 0)
        
        if loss_pct > 80 and cv > 2.0:
            return "Very High"
        elif loss_pct > 70 and cv > 1.5:
            return "High"
        elif loss_pct > 60 and cv > 1.0:
            return "Medium"
        else:
            return "Low"
    
    def generate_volatility_report(self, output_path: str):
        """Generate detailed volatility report"""
        metrics = self.calculate_comprehensive_volatility()
        if not metrics:
            print("No data available for volatility report.")
            return

        with open(output_path, 'w') as f:
            f.write("VOLATILITY ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Basic Statistics:\n")
            for key, val in metrics['basic_stats'].items():
                f.write(f"  {key}: {val:.4f}\n")
            
            f.write("\nHit Distribution:\n")
            for cat, data in metrics['hit_distribution'].items():
                f.write(f"  {cat}: {data['percentage']:.2f}% ({data['count']} spins)\n")
            
            f.write(f"\nVolatility Classification: {metrics['classification']}\n")
            
            f.write("\nRisk of Ruin (by bankroll in units):\n")
            for bankroll, ror in metrics['risk_metrics']['risk_of_ruin'].items():
                f.write(f"  {bankroll} units: {ror:.4%}\n")
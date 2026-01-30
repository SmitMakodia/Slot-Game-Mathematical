from itertools import product
import numpy as np
from typing import Dict, List
from .reel_strip import ReelStrip
from .payline_logic import PaylineEvaluator

class RTPCalculator:
    def __init__(self, reel_strip: ReelStrip, evaluator: PaylineEvaluator):
        self.reel = reel_strip
        self.evaluator = evaluator
        self.total_combinations = np.prod(reel_strip.reel_stops)
    
    def calculate_exact_rtp(self, sample_limit: int = 100_000_000) -> Dict:
        if self.total_combinations > sample_limit:
            return self.calculate_theoretical_rtp_monte_carlo(n_spins=1_000_000)
        
        total_return = 0
        winning_combinations = 0
        hit_distribution = {i: 0 for i in range(6)}
        volatility_sum = 0
        
        reel_ranges = [range(stops) for stops in self.reel.reel_stops]
        
        for combo in product(*reel_ranges):
            grid = self._stops_to_grid(combo)
            result = self.evaluator.evaluate_all_paylines(grid)
            
            win = result['total_win']
            total_return += win
            volatility_sum += win ** 2
            
            win_count = len(result['line_wins'])
            if win_count > 0 or result['scatter_win'] > 0:
                winning_combinations += 1
            
            hit_dist_idx = min(win_count + (1 if result['scatter_win'] > 0 else 0), 5)
            hit_distribution[hit_dist_idx] += 1
        
        bet_per_spin = len(self.evaluator.paylines) 
        if bet_per_spin == 0: bet_per_spin = 20
        
        rtp = (total_return / self.total_combinations) / bet_per_spin * 100
        hit_freq = (winning_combinations / self.total_combinations) * 100
        
        avg_win = total_return / self.total_combinations
        variance = (volatility_sum / self.total_combinations) - (avg_win ** 2)
        
        return {
            'rtp': rtp,
            'hit_frequency': hit_freq,
            'variance': variance,
            'std_dev': np.sqrt(variance),
            'hit_distribution': hit_distribution,
            'total_combinations': self.total_combinations,
            'method': 'Exact Combinatorial'
        }
    
    def calculate_theoretical_rtp_monte_carlo(self, n_spins: int = 10_000_000) -> Dict:
        rng = np.random.default_rng(seed=42)
        total_return = 0
        bet_per_spin = len(self.evaluator.paylines)
        if bet_per_spin == 0: bet_per_spin = 20
        total_bet = n_spins * bet_per_spin
        
        wins = 0
        win_amounts = []
        
        batch_size = 10000
        batches = n_spins // batch_size
        
        for _ in range(n_spins):
            grid = []
            for reel_idx in range(5):
                reel_data = self.reel.cumulative_weights[reel_idx]
                col_symbols = []
                for _ in range(3):
                    stop = rng.integers(0, reel_data['total'])
                    symbol = self.reel.get_symbol_at_stop(reel_idx, stop)
                    col_symbols.append(symbol)
                grid.append(col_symbols)
            
            result = self.evaluator.evaluate_all_paylines(grid)
            
            total_return += result['total_win']
            if result['total_win'] > 0:
                wins += 1
            win_amounts.append(result['total_win'])
        
        rtp = (total_return / total_bet) * 100
        hit_freq = (wins / n_spins) * 100
        variance = np.var(win_amounts)
        
        std_error = np.std(win_amounts) / np.sqrt(n_spins)
        ci_lower = rtp - 1.96 * (std_error / bet_per_spin * 100)
        ci_upper = rtp + 1.96 * (std_error / bet_per_spin * 100)
        
        return {
            'rtp': rtp,
            'hit_frequency': hit_freq,
            'variance': variance,
            'std_dev': np.sqrt(variance),
            'confidence_interval': (ci_lower, ci_upper),
            'method': 'Monte Carlo',
            'n_spins': n_spins
        }
    
    def _stops_to_grid(self, stops: tuple) -> List[List[str]]:
        grid = []
        for reel_idx, stop in enumerate(stops):
            symbol = self.reel.get_symbol_at_stop(reel_idx, stop)
            grid.append([symbol]) 
        return grid
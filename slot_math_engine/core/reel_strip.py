import numpy as np
import json
from typing import List, Dict, Tuple

class ReelStrip:
    def __init__(self, config_path: str):
        if isinstance(config_path, dict):
            self.config = config_path
        else:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        self.symbols = self.config['symbols']
        self.reel_stops = self.config['virtual_reel_stops']
        self.build_cumulative_weights()
    
    def build_cumulative_weights(self):
        self.cumulative_weights = []
        for reel_idx in range(5):
            weights = []
            symbols = []
            for sym_name, sym_data in self.symbols.items():
                weight_val = sym_data['weight']
                if isinstance(weight_val, list):
                    weight = weight_val[reel_idx]
                else:
                    weight = weight_val
                    
                weights.append(weight)
                symbols.append(sym_name)
            
            cumsum = np.cumsum(weights)
            total = cumsum[-1]
            self.cumulative_weights.append({
                'cumsum': cumsum,
                'total': total,
                'symbols': symbols,
                'weights': weights
            })
    
    def get_symbol_at_stop(self, reel_idx: int, stop: int) -> str:
        reel_data = self.cumulative_weights[reel_idx]
        cumsum = reel_data['cumsum']
        
        idx = np.searchsorted(cumsum, stop + 1)
        return reel_data['symbols'][idx]
    
    def get_random_symbols(self, rng: np.random.Generator) -> List[str]:
        result = []
        for reel_idx in range(5):
            reel_data = self.cumulative_weights[reel_idx]
            random_stop = rng.integers(0, reel_data['total'])
            symbol = self.get_symbol_at_stop(reel_idx, random_stop)
            result.append(symbol)
        return result
    
    def get_symbol_probability(self, reel_idx: int, symbol_name: str) -> float:
        reel_data = self.cumulative_weights[reel_idx]
        try:
            idx = reel_data['symbols'].index(symbol_name)
            return reel_data['weights'][idx] / reel_data['total']
        except ValueError:
            return 0.0
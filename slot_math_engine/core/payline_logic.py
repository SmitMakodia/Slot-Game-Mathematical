from typing import List, Dict, Tuple
import numpy as np

class PaylineEvaluator:
    def __init__(self, symbols_config: Dict, paylines: List[List[Tuple[int, int]]]):
        self.symbols = symbols_config
        self.paylines = paylines
        self.wild_symbol = 'WILD'
        self.scatter_symbol = 'SCATTER'
    
    def evaluate_single_payline(self, reel_symbols: List[str], line_idx: int) -> Tuple[int, str]:
        line_symbols = reel_symbols
        
        base_idx = 0
        base_symbol = line_symbols[0]
        
        if base_symbol == self.wild_symbol:
            found_non_wild = False
            for i in range(1, 5):
                if line_symbols[i] != self.wild_symbol and line_symbols[i] != self.scatter_symbol:
                    base_symbol = line_symbols[i]
                    found_non_wild = True
                    break
            if not found_non_wild:
                 base_symbol = self.wild_symbol
        
        match_count = 0
        for i in range(5):
            current = line_symbols[i]
            if current == base_symbol or (current == self.wild_symbol and base_symbol != self.scatter_symbol):
                match_count += 1
            elif base_symbol == self.wild_symbol and current != self.scatter_symbol:
                 break
            else:
                break
        
        if match_count > 0:
            payout_list = self.symbols[base_symbol]['payout']
            if match_count < len(payout_list):
                payout = payout_list[match_count]
            else:
                payout = 0
            
            if payout > 0:
                combo_name = f"{match_count} {base_symbol}"
                return payout, combo_name
        
        return 0, "Loss"
    
    def evaluate_all_paylines(self, grid: List[List[str]]) -> Dict:
        total_win = 0
        line_wins = []
        
        for line_idx, line in enumerate(self.paylines):
            line_symbols = []
            for reel_idx, row_idx in line:
                if reel_idx < len(grid) and row_idx < len(grid[reel_idx]):
                     line_symbols.append(grid[reel_idx][row_idx])
                else:
                    line_symbols.append("ERROR") 

            win, combo = self.evaluate_single_payline(line_symbols, line_idx)
            
            if win > 0:
                total_win += win
                line_wins.append({
                    'payline_idx': line_idx,
                    'win': win,
                    'combo': combo,
                    'symbols': line_symbols
                })
        
        all_symbols = [sym for reel in grid for sym in reel]
        scatter_count = all_symbols.count(self.scatter_symbol)
        
        scatter_win = 0
        scatter_payouts = self.symbols.get(self.scatter_symbol, {}).get('payout', [])
        if scatter_count < len(scatter_payouts):
            scatter_win = scatter_payouts[scatter_count]
            total_win += scatter_win
        
        return {
            'total_win': total_win,
            'line_wins': line_wins,
            'scatter_win': scatter_win,
            'scatter_count': scatter_count
        }
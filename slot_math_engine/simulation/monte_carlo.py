import numpy as np
import sqlite3
from datetime import datetime
from typing import Dict, List
import json
from tqdm import tqdm

class MonteCarloSimulator:
    def __init__(self, reel_strip, evaluator, db_path="simulation_results.db"):
        self.reel = reel_strip
        self.evaluator = evaluator
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spin_number INTEGER,
                total_win INTEGER,
                line_wins TEXT,
                scatter_win INTEGER,
                symbols_seen TEXT,
                is_bonus_trigger BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS convergence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_size INTEGER,
                rtp REAL,
                hit_freq REAL,
                std_dev REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run_simulation(self, n_spins: int = 10_000_000, batch_size: int = 100_000):
        rng = np.random.default_rng(seed=42)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_win = 0
        bet_per_spin = len(self.evaluator.paylines)
        if bet_per_spin == 0: bet_per_spin = 20
        total_bet = 0
        
        wins_count = 0
        win_amounts = []
        
        print(f"Starting simulation of {n_spins:,} spins...")
        
        current_spin_global = 0
        
        for batch_start in tqdm(range(0, n_spins, batch_size)):
            batch_end = min(batch_start + batch_size, n_spins)
            batch_data = []
            
            batch_wins = 0
            
            for spin_num in range(batch_start, batch_end):
                grid = []
                symbols_flat = []
                
                for reel_idx in range(5):
                    reel_data = self.reel.cumulative_weights[reel_idx]
                    col_symbols = []
                    for _ in range(3):
                        stop = rng.integers(0, reel_data['total'])
                        symbol = self.reel.get_symbol_at_stop(reel_idx, stop)
                        col_symbols.append(symbol)
                        symbols_flat.append(symbol)
                    grid.append(col_symbols)
                
                result = self.evaluator.evaluate_all_paylines(grid)
                win = result['total_win']
                
                total_win += win
                total_bet += bet_per_spin
                if win > 0:
                    wins_count += 1
                win_amounts.append(win)
                
                batch_data.append((
                    spin_num,
                    int(win),
                    json.dumps(result['line_wins']),
                    int(result['scatter_win']),
                    json.dumps(symbols_flat),
                    result['scatter_count'] >= 3
                ))
            
            cursor.executemany('''
                INSERT INTO spins (spin_number, total_win, line_wins, scatter_win, symbols_seen, is_bonus_trigger)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', batch_data)
            conn.commit()
            
            if batch_end % 1_000_000 == 0 or batch_end == n_spins:
                current_rtp = (total_win / total_bet) * 100 if total_bet > 0 else 0
                current_hit = (wins_count / batch_end) * 100 if batch_end > 0 else 0
                current_std = np.std(win_amounts) if win_amounts else 0
                
                cursor.execute('''
                    INSERT INTO convergence (sample_size, rtp, hit_freq, std_dev)
                    VALUES (?, ?, ?, ?)
                ''', (batch_end, current_rtp, current_hit, current_std))
                conn.commit()
        
        conn.close()
        
        final_rtp = (total_win / total_bet) * 100 if total_bet > 0 else 0
        final_hit_freq = (wins_count / n_spins) * 100 if n_spins > 0 else 0
        final_std = np.std(win_amounts) if win_amounts else 0
        variance = np.var(win_amounts) if win_amounts else 0
        
        z_score = 1.96
        margin_error = z_score * (final_std / np.sqrt(n_spins)) if n_spins > 0 else 0
        ci_lower = final_rtp - (margin_error / bet_per_spin * 100)
        ci_upper = final_rtp + (margin_error / bet_per_spin * 100)
        
        return {
            'total_spins': n_spins,
            'rtp': final_rtp,
            'hit_frequency': final_hit_freq,
            'std_dev': final_std,
            'variance': variance,
            'confidence_interval_95': (ci_lower, ci_upper),
            'margin_of_error': margin_error
        }
    
    def analyze_convergence(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT sample_size, rtp FROM convergence ORDER BY sample_size')
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return {}
        
        sample_sizes = [row[0] for row in data]
        rtps = [row[1] for row in data]
        
        return {
            'sample_sizes': sample_sizes,
            'rtps': rtps,
            'convergence_stable': self._check_stability(rtps),
            'final_deviation': np.std(rtps[-10:]) if len(rtps) >= 10 else np.std(rtps)
        }
    
    def _check_stability(self, rtps: List[float], threshold: float = 0.1) -> bool:
        if len(rtps) < 10:
            return False
        recent = rtps[-10:]
        return max(recent) - min(recent) < threshold
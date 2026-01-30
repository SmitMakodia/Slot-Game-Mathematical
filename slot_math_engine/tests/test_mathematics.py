import unittest
import numpy as np
import sys
import os
import json

# Handle import paths to find 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.reel_strip import ReelStrip
from core.rtp_calculator import RTPCalculator
from core.payline_logic import PaylineEvaluator

class TestReelMathematics(unittest.TestCase):
    def setUp(self):
        """Create test configuration"""
        self.test_config = {
            "game_name": "Test Slot",
            "reels": 5,
            "rows": 3,
            "paylines": 20,
            "symbols": {
                "WILD": {"id": 0, "weight": [1, 1, 1, 1, 1], "payout": [0, 0, 0, 100, 500, 2000]},
                "A": {"id": 1, "weight": [2, 2, 2, 2, 2], "payout": [0, 0, 0, 50, 200, 1000]},
                "K": {"id": 2, "weight": [3, 3, 3, 3, 3], "payout": [0, 0, 0, 20, 100, 500]}
            },
            "virtual_reel_stops": [6, 6, 6, 6, 6]
        }
        
        self.reel = ReelStrip(self.test_config)
    
    def test_reel_probabilities_sum_to_one(self):
        """Verify that symbol probabilities on each reel sum to 1.0"""
        for reel_idx in range(5):
            total_prob = 0
            for sym_name in self.reel.symbols.keys():
                prob = self.reel.get_symbol_probability(reel_idx, sym_name)
                total_prob += prob
            
            self.assertAlmostEqual(total_prob, 1.0, places=6, 
                                 msg=f"Reel {reel_idx} probabilities sum to {total_prob}, not 1.0")
    
    def test_symbol_probability_calculation(self):
        """Test exact probability calculation for known configuration"""
        # Reel 0: WILD weight 1, A weight 2, K weight 3, Total = 6
        wild_prob = self.reel.get_symbol_probability(0, "WILD")
        self.assertAlmostEqual(wild_prob, 1/6, places=6)
        
        a_prob = self.reel.get_symbol_probability(0, "A")
        self.assertAlmostEqual(a_prob, 2/6, places=6)
    
    def test_cumulative_weights_construction(self):
        """Verify cumulative weight arrays are built correctly"""
        reel_data = self.reel.cumulative_weights[0]
        self.assertEqual(reel_data['total'], 6)
        self.assertEqual(list(reel_data['cumsum']), [1, 3, 6])  # WILD:1, A:1+2=3, K:3+3=6

class TestPaylineEvaluation(unittest.TestCase):
    def setUp(self):
        self.config = {
            "WILD": {"payout": [0, 0, 0, 100, 500, 2000]},
            "A": {"payout": [0, 0, 0, 50, 200, 1000]},
            "SCATTER": {"payout": [0, 0, 0, 5, 20, 100]}
        }
        self.paylines = [[[i, 1] for i in range(5)]] # 1 line
        self.evaluator = PaylineEvaluator(self.config, self.paylines)

    def test_wild_substitution(self):
        """Test that WILD substitutes correctly for other symbols"""
        symbols = ["WILD", "A", "A", "A", "A"]
        # Logic: First symbol is WILD. Search for first non-wild: 'A'.
        # Line becomes effectively 5 As (since WILD matches A).
        win, combo = self.evaluator.evaluate_single_payline(symbols, 0)
        self.assertEqual(win, 1000)
    
    def test_left_to_right_pay(self):
        """Verify only left-to-right matches count"""
        symbols = ["A", "A", "K", "A", "A"]  # 2 A's, then break
        win, combo = self.evaluator.evaluate_single_payline(symbols, 0)
        self.assertEqual(win, 0) # 2 matches pay 0 in config

class TestBonusMathematics(unittest.TestCase):
    def test_free_spins_trigger_probability(self):
        """Test binomial calculation for scatter triggers"""
        # This test relies on internal logic of BonusMathematics
        pass

if __name__ == '__main__':
    unittest.main()

import numpy as np
from typing import Dict, List

class BonusMathematics:
    def __init__(self, reel_strip, base_game_evaluator):
        self.reel = reel_strip
        self.base = base_game_evaluator
        
    def calculate_free_spins_math(self, 
                                  trigger_symbol: str = "SCATTER",
                                  min_triggers: int = 3,
                                  free_spins_awarded: int = 10,
                                  retrigger_spins: int = 5) -> Dict:
        
        scatter_probs = [self.reel.get_symbol_probability(i, trigger_symbol) 
                        for i in range(5)]
        
        from itertools import product
        trigger_probs = {3: 0.0, 4: 0.0, 5: 0.0}
        
        for pattern in product([0, 1], repeat=5):
            count = sum(pattern)
            if count >= 3:
                prob = 1.0
                for i, is_scatter in enumerate(pattern):
                    p = scatter_probs[i]
                    prob *= p if is_scatter else (1 - p)
                trigger_probs[count] += prob

        base_trigger_prob = sum(trigger_probs.values())
        
        base_win_per_spin = self.calculate_base_game_ev()
        
        retrigger_prob = base_trigger_prob 
        
        if retrigger_prob >= 1:
            expected_spins = float('inf') 
        else:
            expected_spins = free_spins_awarded + retrigger_spins * (retrigger_prob / (1 - retrigger_prob))
        
        total_bonus_ev = base_win_per_spin * expected_spins
        
        bonus_contribution = base_trigger_prob * total_bonus_ev
        
        return {
            'trigger_probabilities': {
                '3_scatters': trigger_probs[3],
                '4_scatters': trigger_probs[4],
                '5_scatters': trigger_probs[5],
                'total_trigger_prob': base_trigger_prob
            },
            'base_win_per_spin': base_win_per_spin,
            'expected_spins': expected_spins,
            'total_bonus_ev': total_bonus_ev,
            'contribution_to_rtp': bonus_contribution,
            'contribution_percentage': (bonus_contribution / 20) * 100
        }
    
    def calculate_pick_me_bonus(self, 
                               options: List[Dict],
                               picks_allowed: int = 1) -> Dict:
        total_weight = sum(opt['weight'] for opt in options)
        
        if total_weight != 1.0 and total_weight > 0:
            options = [{**opt, 'weight': opt['weight']/total_weight} for opt in options]
        
        ev_per_pick = sum(opt['prize'] * opt['weight'] for opt in options)
        
        if picks_allowed > 1:
            ev_total = self._calculate_multi_pick_ev(options, picks_allowed)
        else:
            ev_total = ev_per_pick
        
        return {
            'expected_value': ev_total,
            'options': options,
            'variance': self._calculate_pick_variance(options, ev_per_pick),
            'max_possible': max((opt['prize'] for opt in options), default=0),
            'min_possible': min((opt['prize'] for opt in options), default=0)
        }
    
    def _calculate_multi_pick_ev(self, options: List[Dict], picks: int) -> float:
        if picks == 0:
            return 0
        
        total_ev = 0
        
        for i, first_pick in enumerate(options):
            prob = first_pick['weight']
            immediate_value = first_pick['prize']
            
            if picks > 1:
                remaining = [opt for j, opt in enumerate(options) if j != i]
                total_rem = sum(opt['weight'] for opt in remaining)
                if total_rem > 0:
                    remaining = [{**opt, 'weight': opt['weight']/total_rem} for opt in remaining]
                    future_ev = self._calculate_multi_pick_ev(remaining, picks - 1)
                else:
                    future_ev = 0
            else:
                future_ev = 0
            
            total_ev += prob * (immediate_value + future_ev)
        
        return total_ev
    
    def _calculate_pick_variance(self, options: List[Dict], expected_value: float) -> float:
        variance = sum(
            opt['weight'] * (opt['prize'] - expected_value) ** 2 
            for opt in options
        )
        return variance
    
    def calculate_base_game_ev(self) -> float:
        return 15.0
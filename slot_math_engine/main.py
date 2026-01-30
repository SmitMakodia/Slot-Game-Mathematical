#!/usr/bin/env python3
"""
Slot Game Mathematical Modeling Engine
Main Entry Point for CLI Operations
"""

import argparse
import sys
import os
import json
from datetime import datetime
import numpy as np
import pandas as pd

# Add core to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.reel_strip import ReelStrip
from core.rtp_calculator import RTPCalculator
from core.payline_logic import PaylineEvaluator
from core.bonus_math import BonusMathematics
from simulation.monte_carlo import MonteCarloSimulator
from analysis.volatility_metrics import VolatilityAnalyzer
from reporting.par_sheet_generator import PARSheetGenerator

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, 'data', 'reel_configs', 'base_game.json')

def setup_directories():
    """Create necessary data directories if they don't exist"""
    # Create output directories in CWD, but data might be in package or CWD
    dirs = ['results', 'reports']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Only create data dirs if we are initializing or they don't exist in package
    if not os.path.exists(os.path.dirname(DEFAULT_CONFIG_PATH)):
         os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)

def create_default_config():
    """Create default game configuration for testing"""
    config = {
        "game_name": "Zynga Demo Slot - Mathematician Edition",
        "reels": 5,
        "rows": 3,
        "paylines": 20,
        "bet_per_line": 1,
        "symbols": {
            "WILD": {
                "id": 0,
                "weight": [2, 2, 2, 2, 2],
                "payout": [0, 0, 100, 500, 2000]
            },
            "SCATTER": {
                "id": 1,
                "weight": [3, 3, 3, 3, 3],
                "payout": [0, 0, 5, 20, 100],
                "bonus_trigger": True
            },
            "SYMBOL_A": {
                "id": 2,
                "weight": [10, 8, 6, 4, 2],
                "payout": [0, 0, 20, 80, 400]
            },
            "SYMBOL_K": {
                "id": 3,
                "weight": [12, 10, 8, 6, 4],
                "payout": [0, 0, 10, 40, 200]
            },
            "SYMBOL_Q": {
                "id": 4,
                "weight": [15, 12, 10, 8, 6],
                "payout": [0, 0, 5, 30, 150]
            },
            "SYMBOL_J": {
                "id": 5,
                "weight": [20, 15, 12, 10, 8],
                "payout": [0, 0, 5, 20, 100]
            },
            "SYMBOL_10": {
                "id": 6,
                "weight": [25, 20, 15, 12, 10],
                "payout": [0, 0, 2, 10, 50]
            }
        },
        "virtual_reel_stops": [72, 72, 72, 72, 72]
    }
    return config

def cmd_analyze(args):
    """Run theoretical analysis on configuration"""
    print(f"Loading configuration from {args.config}...")
    reel = ReelStrip(args.config)
    
    print(f"Reel stops: {reel.reel_stops}")
    print(f"Total combinations: {np.prod(reel.reel_stops):,}")
    
    # Define standard paylines (20 lines)
    # 0: Top, 1: Middle, 2: Bottom
    paylines_def = [
        [1,1,1,1,1], [0,0,0,0,0], [2,2,2,2,2], [0,1,2,1,0], [2,1,0,1,2],
        [0,0,1,0,0], [2,2,1,2,2], [1,2,2,2,1], [1,0,0,0,1], [1,0,1,0,1],
        [1,2,1,2,1], [0,1,0,1,0], [2,1,2,1,2], [0,1,1,1,0], [2,1,1,1,2],
        [0,2,0,2,0], [2,0,2,0,2], [0,2,2,2,0], [2,0,0,0,2], [0,0,2,0,0]
    ]
    paylines = []
    for p in paylines_def:
        paylines.append([[i, p[i]] for i in range(5)])
    
    evaluator = PaylineEvaluator(reel.config['symbols'], paylines)
    calculator = RTPCalculator(reel, evaluator)
    
    print("Calculating theoretical RTP...")
    result = calculator.calculate_exact_rtp(sample_limit=args.sample_limit)
    
    print("\n" + "="*50)
    print("THEORETICAL ANALYSIS RESULTS")
    print("="*50)
    print(f"RTP: {result['rtp']:.4f}%")
    print(f"Hit Frequency: {result['hit_frequency']:.4f}%")
    print(f"Variance: {result['variance']:.4f}")
    print(f"Std Dev: {result['std_dev']:.4f}")
    print(f"Method: {result.get('method', 'Exact Combinatorial')}")
    
    if 'total_combinations' in result:
        print(f"Total combinations evaluated: {result['total_combinations']:,}")
    
    # Save results
    output_file = f"results/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        # Convert numpy types to native Python for JSON serialization
        def default(o):
            if isinstance(o, np.integer):
                return int(o)
            if isinstance(o, np.floating):
                return float(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
            return str(o)
        json.dump(result, f, indent=2, default=default)
    print(f"\nResults saved to: {output_file}")

def cmd_simulate(args):
    """Run Monte Carlo simulation"""
    print(f"Initializing simulation with {args.spins:,} spins...")
    
    reel = ReelStrip(args.config)
    # Standard paylines
    paylines_def = [
        [1,1,1,1,1], [0,0,0,0,0], [2,2,2,2,2], [0,1,2,1,0], [2,1,0,1,2],
        [0,0,1,0,0], [2,2,1,2,2], [1,2,2,2,1], [1,0,0,0,1], [1,0,1,0,1],
        [1,2,1,2,1], [0,1,0,1,0], [2,1,2,1,2], [0,1,1,1,0], [2,1,1,1,2],
        [0,2,0,2,0], [2,0,2,0,2], [0,2,2,2,0], [2,0,0,0,2], [0,0,2,0,0]
    ]
    paylines = []
    for p in paylines_def:
        paylines.append([[i, p[i]] for i in range(5)])
        
    evaluator = PaylineEvaluator(reel.config['symbols'], paylines)
    simulator = MonteCarloSimulator(reel, evaluator, db_path=args.database)
    
    print("Running simulation (this may take several minutes)...")
    results = simulator.run_simulation(n_spins=args.spins)
    
    print("\n" + "="*50)
    print("MONTE CARLO SIMULATION RESULTS")
    print("="*50)
    print(f"Total Spins: {results['total_spins']:,}")
    print(f"Simulated RTP: {results['rtp']:.4f}%")
    print(f"95% Confidence Interval: [{results['confidence_interval_95'][0]:.4f}%, {results['confidence_interval_95'][1]:.4f}%]")
    print(f"Margin of Error: ±{results['margin_of_error']:.4f}%")
    print(f"Hit Frequency: {results['hit_frequency']:.4f}%")
    print(f"Standard Deviation: {results['std_dev']:.4f}")
    
    # Convergence analysis
    conv = simulator.analyze_convergence()
    if conv:
        print(f"Convergence Stability: {'Stable' if conv['convergence_stable'] else 'Unstable'}")
        print(f"Final Deviation: {conv['final_deviation']:.6f}")

def cmd_par_sheet(args):
    """Generate PAR sheet"""
    print("Generating PAR Sheet...")
    
    reel = ReelStrip(args.config)
    # Standard paylines
    paylines_def = [
        [1,1,1,1,1], [0,0,0,0,0], [2,2,2,2,2], [0,1,2,1,0], [2,1,0,1,2],
        [0,0,1,0,0], [2,2,1,2,2], [1,2,2,2,1], [1,0,0,0,1], [1,0,1,0,1],
        [1,2,1,2,1], [0,1,0,1,0], [2,1,2,1,2], [0,1,1,1,0], [2,1,1,1,2],
        [0,2,0,2,0], [2,0,2,0,2], [0,2,2,2,0], [2,0,0,0,2], [0,0,2,0,0]
    ]
    paylines = []
    for p in paylines_def:
        paylines.append([[i, p[i]] for i in range(5)])
    evaluator = PaylineEvaluator(reel.config['symbols'], paylines)
    calculator = RTPCalculator(reel, evaluator)
    
    # Calculate stats (Fast approximation via sim for the report numbers if exact is too slow)
    stats = calculator.calculate_theoretical_rtp_monte_carlo(n_spins=100_000)
    
    # Override with calculator for PAR generation
    calculator.rtp = stats['rtp']
    calculator.hit_frequency = stats['hit_frequency']
    calculator.variance = stats['variance']
    calculator.std_dev = stats['std_dev']
    
    generator = PARSheetGenerator(calculator, reel)
    output_path = args.output or f"reports/PAR_Sheet_{datetime.now().strftime('%Y%m%d')}.xlsx"
    generator.generate_full_par_sheet(output_path)
    
    print(f"PAR Sheet generated: {output_path}")

def cmd_dashboard(args):
    """Launch Streamlit dashboard"""
    import subprocess
    print("Launching Streamlit dashboard...")
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    subprocess.run(["streamlit", "run", dashboard_path, "--server.port", str(args.port)])

def cmd_bonus_math(args):
    """Calculate bonus feature mathematics"""
    reel = ReelStrip(args.config)
    # Standard paylines
    paylines_def = [
        [1,1,1,1,1], [0,0,0,0,0], [2,2,2,2,2], [0,1,2,1,0], [2,1,0,1,2],
        [0,0,1,0,0], [2,2,1,2,2], [1,2,2,2,1], [1,0,0,0,1], [1,0,1,0,1],
        [1,2,1,2,1], [0,1,0,1,0], [2,1,2,1,2], [0,1,1,1,0], [2,1,1,1,2],
        [0,2,0,2,0], [2,0,2,0,2], [0,2,2,2,0], [2,0,0,0,2], [0,0,2,0,0]
    ]
    paylines = []
    for p in paylines_def:
        paylines.append([[i, p[i]] for i in range(5)])
    evaluator = PaylineEvaluator(reel.config['symbols'], paylines)
    bonus = BonusMathematics(reel, evaluator)
    
    print("="*50)
    print("BONUS MATHEMATICS ANALYSIS")
    print("="*50)
    
    free_spins = bonus.calculate_free_spins_math()
    print("\nFree Spins Feature:")
    print(f"  Trigger Probability (3+ scatters): {free_spins['trigger_probabilities']['total_trigger_prob']:.6f} ({free_spins['trigger_probabilities']['total_trigger_prob']*100:.4f}%)")
    print(f"  Expected Spins (with retrigger): {free_spins['expected_spins']:.2f}")
    print(f"  Total Bonus EV: {free_spins['total_bonus_ev']:.2f} credits")
    print(f"  Contribution to RTP: {free_spins['contribution_percentage']:.4f}%")
    
    # Pick bonus
    pick = bonus.calculate_pick_me_bonus([
        {'prize': 10, 'weight': 0.4},
        {'prize': 25, 'weight': 0.3},
        {'prize': 50, 'weight': 0.2},
        {'prize': 100, 'weight': 0.09},
        {'prize': 500, 'weight': 0.01}
    ])
    print(f"\nPick-Me Bonus:")
    print(f"  Expected Value: {pick['expected_value']:.2f} credits")
    print(f"  Variance: {pick['variance']:.2f}")
    print(f"  Max Prize: {pick['max_possible']}")

def cmd_export_web(args):
    """Export lightweight dashboard data from heavy DB"""
    print("Exporting lightweight dashboard data...")
    db_path = args.database
    
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        return

    try:
        # Initialize Analyzer
        analyzer = VolatilityAnalyzer(db_path)
        
        # 1. Calculate Volatility Metrics
        print("Calculating volatility metrics...")
        metrics = analyzer.calculate_comprehensive_volatility()
        
        # 2. Get Convergence Data
        print("Extracting convergence trends...")
        import sqlite3
        conn = sqlite3.connect(db_path)
        df_conv = pd.read_sql_query("SELECT sample_size, rtp, hit_freq FROM convergence ORDER BY sample_size", conn)
        
        # 3. Get Win Distribution (Histogram Bins)
        print("Computing win distribution histograms...")
        # Get raw wins > 0
        df_wins = pd.read_sql_query("SELECT total_win FROM spins WHERE total_win > 0", conn)
        conn.close()
        
        # Create Histogram Data (Binning) to avoid saving raw list
        if not df_wins.empty:
            hist_counts, bin_edges = np.histogram(df_wins['total_win'], bins=50)
            hist_data = {
                'counts': hist_counts.tolist(),
                'bin_edges': bin_edges.tolist()
            }
        else:
            hist_data = None

        # 4. Construct JSON Structure
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_spins': int(df_conv['sample_size'].iloc[-1]) if not df_conv.empty else 0,
            'sim_rtp': float(df_conv['rtp'].iloc[-1]) if not df_conv.empty else 0,
            'hit_freq': float(df_conv['hit_freq'].iloc[-1]) if not df_conv.empty else 0,
            'metrics': metrics,
            'convergence': df_conv.to_dict(orient='list'),
            'win_distribution': hist_data
        }
        
        # Save
        output_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'dashboard_data.json')
        with open(output_path, 'w') as f:
            # Handle numpy types
            def default(o):
                if isinstance(o, np.integer): return int(o)
                if isinstance(o, np.floating): return float(o)
                if isinstance(o, np.ndarray): return o.tolist()
                return str(o)
            json.dump(export_data, f, indent=2, default=default)
            
        print(f"Success! Lightweight data saved to: {output_path}")
        print("You can now deploy this JSON file with your dashboard.")
        
    except Exception as e:
        print(f"Export failed: {e}")
        import traceback
        traceback.print_exc()

def cmd_export_excel(args):
    """Export simulation data to Excel (Limited rows)"""
    print(f"Exporting data to Excel (Limit: {args.limit} rows)...")
    db_path = args.database
    
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        return
        
    try:
        import sqlite3
        import pandas as pd
        conn = sqlite3.connect(db_path)
        
        # 1. Summary Sheet
        print("Reading convergence data...")
        df_conv = pd.read_sql_query("SELECT * FROM convergence", conn)
        
        # 2. Raw Spins (Limited)
        print(f"Reading last {args.limit} spins...")
        df_spins = pd.read_sql_query(f"SELECT * FROM spins ORDER BY id DESC LIMIT {args.limit}", conn)
        
        conn.close()
        
        # Write to Excel
        output_file = args.output or f"results/Simulation_Export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            df_conv.to_excel(writer, sheet_name='Convergence', index=False)
            df_spins.to_excel(writer, sheet_name='Raw Spins Sample', index=False)
            
        print(f"Export complete: {output_file}")
        
    except Exception as e:
        print(f"Excel export failed: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Slot Game Mathematical Modeling Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run theoretical RTP analysis')
    analyze_parser.add_argument('--config', default=DEFAULT_CONFIG_PATH,
                               help='Path to reel configuration JSON')
    analyze_parser.add_argument('--sample-limit', type=int, default=100_000_000,
                               help='Maximum combinations to calculate exactly')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Simulate command
    sim_parser = subparsers.add_parser('simulate', help='Run Monte Carlo simulation')
    sim_parser.add_argument('--config', default=DEFAULT_CONFIG_PATH)
    sim_parser.add_argument('--spins', type=int, default=1_000_000,
                           help='Number of spins to simulate')
    sim_parser.add_argument('--database', default='simulation_results.db',
                           help='SQLite database path for results')
    sim_parser.set_defaults(func=cmd_simulate)
    
    # PAR sheet command
    par_parser = subparsers.add_parser('par-sheet', help='Generate regulatory PAR sheet')
    par_parser.add_argument('--config', default=DEFAULT_CONFIG_PATH)
    par_parser.add_argument('--output', '-o', help='Output Excel file path')
    par_parser.set_defaults(func=cmd_par_sheet)
    
    # Dashboard command
    dash_parser = subparsers.add_parser('dashboard', help='Launch interactive web dashboard')
    dash_parser.add_argument('--port', type=int, default=8501,
                            help='Port for Streamlit server')
    dash_parser.set_defaults(func=cmd_dashboard)
    
    # Bonus math command
    bonus_parser = subparsers.add_parser('bonus-math', help='Calculate bonus feature mathematics')
    bonus_parser.add_argument('--config', default=DEFAULT_CONFIG_PATH)
    bonus_parser.set_defaults(func=cmd_bonus_math)
    
    # Export Web command
    web_parser = subparsers.add_parser('export-web', help='Prepare lightweight JSON for deployment')
    web_parser.add_argument('--database', default='simulation_results.db')
    web_parser.set_defaults(func=cmd_export_web)
    
    # Export Excel command
    xls_parser = subparsers.add_parser('export-excel', help='Export data sample to Excel')
    xls_parser.add_argument('--database', default='simulation_results.db')
    xls_parser.add_argument('--limit', type=int, default=100000, help="Row limit for spins")
    xls_parser.add_argument('--output', '-o', help="Output filename")
    xls_parser.set_defaults(func=cmd_export_excel)
    
    # Initialize command (create default config)
    init_parser = subparsers.add_parser('init', help='Initialize project with default configuration')
    init_parser.add_argument('--name', default='base_game', help='Configuration name')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Setup directories
    setup_directories()
    
    # Handle init command separately
    if args.command == 'init':
        config = create_default_config()
        config_path = f'data/reel_configs/{args.name}.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created default configuration: {config_path}")
        return
    
    # Execute command
    try:
        args.func(args)
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found - {e}")
        print("Run 'python main.py init' first to create default configuration")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

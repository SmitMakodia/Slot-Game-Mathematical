import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import json
import sqlite3
import time
import base64

# Add parent dir to path to find core packages
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.reel_strip import ReelStrip
from core.rtp_calculator import RTPCalculator
from core.payline_logic import PaylineEvaluator
from core.bonus_math import BonusMathematics
from simulation.monte_carlo import MonteCarloSimulator
from analysis.volatility_metrics import VolatilityAnalyzer

# --- Page Configuration ---
st.set_page_config(
    page_title="CSGMVE Math Engine",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Professional Casino UI ---
st.markdown("""
<style>
    /* Global Theme Overrides */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
        color: #F0F2F6;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* --- METRIC CARDS --- */
    div[data-testid="metric-container"] {
        background: linear-gradient(180deg, #1F2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: -webkit-linear-gradient(#fff, #9ca3af);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* --- REEL VISUALIZATION --- */
    .machine-container {
        display: flex;
        justify-content: center;
        padding: 25px;
        background: #000;
        border-radius: 20px;
        border: 8px solid #2d3748;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8), inset 0 0 60px rgba(0,0,0,0.9);
        margin-bottom: 20px;
        position: relative;
    }
    
    /* Glass reflection effect */
    .machine-container::after {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 40%;
        background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 100%);
        border-radius: 12px 12px 0 0;
        pointer-events: none;
    }
    
    .reel-frame {
        display: flex;
        gap: 12px;
        padding: 15px;
        background: #111;
        border-radius: 10px;
        border: 2px solid #333;
        box-shadow: inset 0 0 20px #000;
    }

    .reel-col {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .symbol-card {
        width: 110px;
        height: 100px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Courier New', monospace; 
        font-size: 48px;
        font-weight: 900;
        position: relative;
        background: #fff;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
        transition: transform 0.1s;
    }
    
    .symbol-img {
        max-width: 80%;
        max-height: 80%;
        object-fit: contain;
    }

    /* Symbol Specific Styles */
    .sym-wild {
        background-color: #ffffff;
    }
    .sym-scatter {
        background-color: #ffffff;
    }
    
    /* High Pay Letters - Solid Colors, White Font */
    .sym-high-a { 
        background-color: #D32F2F; 
        color: white; 
    }
    .sym-high-k { 
        background-color: #1976D2; 
        color: white; 
    }
    .sym-high-q { 
        background-color: #7B1FA2; 
        color: white; 
    }
    .sym-low-j { 
        background-color: #388E3C; 
        color: white; 
    }
    .sym-low-10 { 
        background-color: #5D4037; 
        color: white; 
    }
    
    .sym-blank {
        background-color: #ffffff; /* Game Blank is White */
        color: transparent;
        border: 1px solid #eee;
    }

    .unloadedtile {
        background-color: #222;
        color: #ff0000;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        font-size: 48px;
    }

</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_resource
def load_config():
    config_path = os.path.join(parent_dir, 'data', 'reel_configs', 'base_game.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return None
    except:
        return None

def load_static_data():
    """Load pre-computed data from JSON for deployment"""
    json_path = os.path.join(current_dir, 'dashboard_data.json')
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return None

def get_db_connection():
    # DB is expected in project root (D:\codes\Slot Game Mathematical\)
    project_root = os.path.dirname(parent_dir)
    db_path = os.path.join(project_root, 'simulation_results.db')
    if os.path.exists(db_path):
        return sqlite3.connect(db_path)
    return None

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

def get_visual_content(raw_name):
    """Returns (content_html, css_class)"""
    # Clean name
    clean = raw_name.replace("SYMBOL_", "")
    
    if raw_name == "BLANK":
        return "", "sym-blank"
        
    if raw_name == "WILD":
        img_path = os.path.join(parent_dir, "images", "joker.png")
        b64 = get_base64_image(img_path)
        if b64:
            return f'<img src="data:image/png;base64,{b64}" class="symbol-img">', "sym-wild"
        return "JOKER", "sym-wild"

    if raw_name == "SCATTER":
        img_path = os.path.join(parent_dir, "images", "diamond.png")
        b64 = get_base64_image(img_path)
        if b64:
            return f'<img src="data:image/png;base64,{b64}" class="symbol-img">', "sym-scatter"
        return "DIAMOND", "sym-scatter"
    
    css_map = {
        "A": "sym-high-a",
        "K": "sym-high-k",
        "Q": "sym-high-q",
        "J": "sym-low-j",
        "10": "sym-low-10"
    }
    
    return clean, css_map.get(clean, "sym-low-10")

def render_machine_html(grid_data):
    """Generates the HTML for the current state of the reels"""
    html = '<div class="machine-container"><div class="reel-frame">'
    for col in grid_data:
        html += '<div class="reel-col">'
        for cell in col:
            content = cell['content']
            css_class = cell['css_class']
            html += f'<div class="symbol-card {css_class}">{content}</div>'
        html += '</div>'
    html += '</div></div>'
    return html

# --- Main App ---
def main():
    config = load_config()
    static_data = load_static_data()
    
    # Sidebar
    with st.sidebar:
        st.title("🎛️ Control Panel")
        
        mode = st.radio("Navigation", [
            "📊 Dashboard Overview",
            "🎮 Live Play Test",
            "📉 Deep Dive Analysis",
            "📜 PAR Sheet Export"
        ])
        
        st.markdown("---")
        st.caption(f"Config: {config['game_name'] if config else 'None'}")
        
        if st.button("🔄 Reload Configuration"):
            st.cache_resource.clear()
            st.rerun()

    if not config:
        st.error("Configuration file not found. Please run 'python main.py init' first.")
        return

    reel = ReelStrip(config)
    # Standard 20 paylines
    paylines_def = [
        [1,1,1,1,1], [0,0,0,0,0], [2,2,2,2,2], [0,1,2,1,0], [2,1,0,1,2],
        [0,0,1,0,0], [2,2,1,2,2], [1,2,2,2,1], [1,0,0,0,1], [1,0,1,0,1],
        [1,2,1,2,1], [0,1,0,1,0], [2,1,2,1,2], [0,1,1,1,0], [2,1,1,1,2],
        [0,2,0,2,0], [2,0,2,0,2], [0,2,2,2,0], [2,0,0,0,2], [0,0,2,0,0]
    ]
    paylines = [[[i, p[i]] for i in range(5)] for p in paylines_def]
    evaluator = PaylineEvaluator(config['symbols'], paylines)

    # --- VIEW: DASHBOARD OVERVIEW ---
    if mode == "📊 Dashboard Overview":
        st.markdown("# 🎰 Casino Math Studio")
        st.markdown("Real-time telemetry and mathematical validation engine.")

        # Load Data (Prefer DB, fallback to Static)
        sim_rtp, total_spins, hit_freq = 0, 0, 0
        df_trend = pd.DataFrame()
        
        conn = get_db_connection()
        if conn:
            try:
                # Check if tables exist
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spins'")
                if cursor.fetchone():
                    df_conv = pd.read_sql("SELECT * FROM convergence ORDER BY sample_size DESC LIMIT 1", conn)
                    df_stats = pd.read_sql("SELECT count(*) as count, avg(total_win) as avg_win FROM spins", conn)
                    
                    sim_rtp = df_conv['rtp'].values[0] if not df_conv.empty else 0
                    total_spins = df_stats['count'].values[0]
                    hit_freq = df_conv['hit_freq'].values[0] if not df_conv.empty else 0
                    
                    df_trend = pd.read_sql("SELECT sample_size, rtp FROM convergence ORDER BY sample_size", conn)
                conn.close()
            except Exception as e:
                st.warning(f"Database error: {e}")
        elif static_data:
            # Use Static Data
            sim_rtp = static_data.get('sim_rtp', 0)
            total_spins = static_data.get('total_spins', 0)
            hit_freq = static_data.get('hit_freq', 0)
            df_trend = pd.DataFrame(static_data.get('convergence', {}))
            st.caption("ℹ️ Viewing static export data (Live DB not found)")
        else:
            st.warning("No simulation data found. Run 'simulate' locally or 'export-web' for deployment.")

        # Top Level Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Theoretical RTP", "94.80%", delta="Target")
        with col2:
            delta_rtp = sim_rtp - 94.80
            st.metric("Simulated RTP", f"{sim_rtp:.2f}%", delta=f"{delta_rtp:.2f}%")
        with col3:
            st.metric("Total Spins Sim", f"{total_spins:,}")
        with col4:
            st.metric("Hit Frequency", f"{hit_freq:.2f}%")

        # Convergence Plot
        st.markdown('<div class="section-header">RTP Convergence Analysis</div>', unsafe_allow_html=True)
        if not df_trend.empty:
            fig = px.line(df_trend, x='sample_size', y='rtp', 
                          title='RTP Convergence over Spins',
                          labels={'sample_size': 'Spins', 'rtp': 'RTP (%)'})
            fig.add_hline(y=94.80, line_dash="dash", line_color="#4CAF50", annotation_text="Theoretical")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#F0F2F6",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#333")
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- VIEW: LIVE PLAY TEST ---
    elif mode == "🎮 Live Play Test":
        st.markdown("# 🎮 Interactive Play Test")
        
        col_ctrl, col_game = st.columns([1, 2])
        
        if 'animating' not in st.session_state:
            st.session_state['animating'] = False
        
        with col_game:
            machine_placeholder = st.empty()
            
            if 'last_spin' in st.session_state and not st.session_state['animating']:
                machine_placeholder.markdown(render_machine_html(st.session_state['last_spin']['grid']), unsafe_allow_html=True)
            elif not st.session_state.get('animating', False):
                # Render unloaded grid
                unloaded_grid = []
                for i in range(5):
                    col = []
                    for j in range(3):
                        col.append({'content': '?', 'css_class': 'unloadedtile'})
                    unloaded_grid.append(col)
                machine_placeholder.markdown(render_machine_html(unloaded_grid), unsafe_allow_html=True)

        with col_ctrl:
            st.markdown("### Controls")
            
            if st.button("🎰 SPIN REELS", type="primary", use_container_width=True, disabled=st.session_state['animating']):
                st.session_state['animating'] = True
                
                rng = np.random.default_rng()
                grid_final = []
                grid_raw = []
                
                for reel_idx in range(5):
                    reel_data = reel.cumulative_weights[reel_idx]
                    col_syms = []
                    col_raw = []
                    for _ in range(3):
                        stop = rng.integers(0, reel_data['total'])
                        sym = reel.get_symbol_at_stop(reel_idx, stop)
                        col_raw.append(sym)
                        
                        content, css = get_visual_content(sym)
                        col_syms.append({
                            'content': content,
                            'css_class': css
                        })
                    grid_final.append(col_syms)
                    grid_raw.append(col_raw)
                
                res = evaluator.evaluate_all_paylines(grid_raw)
                
                # ANIMATION SEQUENCE
                # 1. Show all Unloaded
                unloaded_grid = [[{'content': '?', 'css_class': 'unloadedtile'} for _ in range(3)] for _ in range(5)]
                machine_placeholder.markdown(render_machine_html(unloaded_grid), unsafe_allow_html=True)
                time.sleep(0.3)
                
                # 2. Reveal Reel by Reel
                current_display = unloaded_grid
                for r in range(5):
                    current_display[r] = grid_final[r]
                    machine_placeholder.markdown(render_machine_html(current_display), unsafe_allow_html=True)
                    time.sleep(0.3) # Total approx 1.5s
                
                st.session_state['last_spin'] = {
                    'grid': grid_final,
                    'result': res
                }
                st.session_state['animating'] = False
                st.rerun()

            if 'last_spin' in st.session_state and not st.session_state['animating']:
                res = st.session_state['last_spin']['result']
                st.markdown("---")
                st.markdown("### Spin Result")
                if res['total_win'] > 0:
                    st.success(f"**BIG WIN: {res['total_win']} Credits**")
                    if res['scatter_win'] > 0:
                        st.write(f"✨ Scatter Win: {res['scatter_win']}")
                    
                    if res['line_wins']:
                        with st.expander("Show Winning Lines", expanded=True):
                            for win in res['line_wins']:
                                st.caption(f"Line {win['payline_idx']+1}: {win['combo']} ({win['win']})")
                else:
                    st.markdown("Outcome: No Win")

    # --- VIEW: DEEP DIVE ANALYSIS ---
    elif mode == "📉 Deep Dive Analysis":
        st.markdown("# 📉 Statistical Deep Dive")
        
        tab1, tab2, tab3 = st.tabs(["Win Distribution", "Symbol Math", "Volatility"])
        
        with tab1:
            st.markdown("### Win Size Distribution")
            
            conn = get_db_connection()
            if conn:
                try:
                    df_wins = pd.read_sql("SELECT total_win FROM spins WHERE total_win > 0 LIMIT 10000", conn)
                    conn.close()
                    
                    if not df_wins.empty:
                        fig = px.histogram(df_wins, x="total_win", nbins=50, 
                                         title="Distribution of Winning Spins (Sample 10k)",
                                         color_discrete_sequence=['#4CAF50'])
                        fig.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="#F0F2F6"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    st.error("Database connection error")
            elif static_data and 'win_distribution' in static_data:
                # Reconstruct Histogram from Static Data
                hist = static_data['win_distribution']
                if hist:
                    fig = px.bar(x=hist['bin_edges'][:-1], y=hist['counts'],
                                 title="Distribution of Winning Spins (Full Simulation)",
                                 color_discrete_sequence=['#4CAF50'])
                    fig.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#F0F2F6",
                        xaxis_title="Win Amount",
                        yaxis_title="Count"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No win data available.")

        with tab2:
            st.markdown("### Reel Strip Analysis")
            reel_data = []
            for r_idx in range(5):
                weights = reel.cumulative_weights[r_idx]
                for s, w in zip(weights['symbols'], weights['weights']):
                    clean_s = s.replace("SYMBOL_", "")
                    reel_data.append({'Reel': f"Reel {r_idx+1}", 'Symbol': clean_s, 'Weight': w})
            
            df_reels = pd.DataFrame(reel_data)
            fig = px.bar(df_reels, x="Reel", y="Weight", color="Symbol", 
                         title="Symbol Weight Distribution per Reel")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#F0F2F6"
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.markdown("### Volatility & Risk")
            
            conn = get_db_connection()
            if conn:
                # Live Calc
                project_root = os.path.dirname(parent_dir)
                db_path = os.path.join(project_root, "simulation_results.db")
                analyzer = VolatilityAnalyzer(db_path)
                with st.spinner("Calculating Risk Metrics..."):
                     try:
                        metrics = analyzer.calculate_comprehensive_volatility()
                        if metrics:
                            c1, c2 = st.columns(2)
                            c1.metric("Std Deviation", f"{metrics['basic_stats']['std_dev']:.2f}")
                            c1.metric("Volatility Index", f"{metrics['basic_stats']['volatility_index']:.2f}")
                            c2.write("**Risk of Ruin (Bankroll)**")
                            st.table(pd.DataFrame(metrics['risk_metrics']['risk_of_ruin'].items(), columns=['Bankroll', 'Risk %']))
                     except Exception as e:
                         st.error(f"Error calculating volatility: {e}")
            elif static_data and 'metrics' in static_data:
                # Static Display
                metrics = static_data['metrics']
                c1, c2 = st.columns(2)
                c1.metric("Std Deviation", f"{metrics['basic_stats']['std_dev']:.2f}")
                c1.metric("Volatility Index", f"{metrics['basic_stats']['volatility_index']:.2f}")
                c2.write("**Risk of Ruin (Bankroll)**")
                st.table(pd.DataFrame(metrics['risk_metrics']['risk_of_ruin'].items(), columns=['Bankroll', 'Risk %']))
            else:
                st.warning("No volatility data found.")

    # --- VIEW: PAR SHEET ---
    elif mode == "📜 PAR Sheet Export":
        st.markdown("# 📜 Regulatory PAR Sheet")
        st.markdown("Download standard probability accounting reports.")
        
        st.download_button(
            label="📄 Download Full PAR Sheet (Excel)",
            data=b"Simulated Excel Content",
            file_name="PAR_Sheet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Generate via CLI 'par-sheet' command first"
        )
        
        st.markdown("### Preview: Pay Table Math")
        rows = []
        for sym, data in config['symbols'].items():
            if sym == "BLANK": continue
            rows.append({
                "Symbol": sym.replace("SYMBOL_", ""),
                "5-oak": data['payout'][5] if len(data['payout'])>5 else 0,
                "4-oak": data['payout'][4] if len(data['payout'])>4 else 0,
                "3-oak": data['payout'][3] if len(data['payout'])>3 else 0,
            })
        st.table(pd.DataFrame(rows))

if __name__ == "__main__":
    main()
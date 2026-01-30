# 🎰 Slot Math Engine - User Guide

This guide explains how to use the Slot Math Engine ecosystem, from configuring the math to visualizing it on the Dashboard.

## 🔄 The Workflow

The system is designed to work in a specific order:

1.  **Configure**: Edit `data/reel_configs/base_game.json` to define your reels and payouts.
2.  **Analyze**: Calculate the *Theoretical* math (what should happen).
3.  **Simulate**: Run millions of spins to generate *Actual* data (what actually happens).
4.  **Visualize**: Use the Dashboard to see the results.

---

## 💻 CLI Commands Reference

Run these commands in your terminal (PowerShell/CMD).

### 1. `python slot_math_engine/main.py analyze`
*   **Purpose**: Theoretical Calculation.
*   **What it does**: Reads your JSON config and uses combinatorial math to calculate the exact RTP and Hit Frequency.
*   **Current Profile**: "Zynga Pro Slot (Production v8)"
    *   **Target RTP**: ~95%
    *   **Hit Frequency**: ~47%
*   **When to use**: Whenever you change `base_game.json`.

### 2. `python slot_math_engine/main.py simulate --spins 5000000`
*   **Purpose**: Data Generation.
*   **What it does**: "Plays" the game 5 million times.
*   **Crucial Note**: This populates the `simulation_results.db` database. **The Dashboard will be empty without this!**
*   **Expectation**:
    *   **Simulated RTP**: Should be between 94% - 96%.
    *   **Hit Frequency**: Should be around 47%.

### 3. `python slot_math_engine/main.py dashboard`
*   **Purpose**: Visualization.
*   **What it does**: Launches a local web server (Streamlit) to view the data.
*   **URL**: Usually `http://localhost:8501`.

### 4. `python slot_math_engine/main.py par-sheet`
*   **Purpose**: Regulatory Reporting.
*   **What it does**: Generates a professional Excel file with all the probabilities broken down. Use this to sign off on the math.

### 5. `python slot_math_engine/main.py bonus-math`
*   **Purpose**: Feature Specifics.
*   **What it does**: Calculates stats just for the Free Spins or Bonus Games (e.g., "How often do I trigger the bonus?").

---

## 📊 Dashboard Guide

The Dashboard is divided into 4 sections (Sidebar Navigation):

### 1. 📊 Dashboard Overview
The "Health Monitor" of your game.
*   **Metrics**:
    *   **Theoretical RTP**: Your target (from `analyze`).
    *   **Simulated RTP**: The actual result (from `simulate`).
    *   **Delta**: The difference. Should be close to 0.00%.
*   **Convergence Plot**:
    *   Shows the RTP fluctuating over time. It should start messy and become a flat line. If it never flattens, your game is highly volatile.

### 2. 🎮 Live Play Test
The "Playable Demo".
*   **Spin Button**: Generates a random spin in real-time.
*   **Visual Grid**: Shows the actual symbols on the reels.
*   **Result Panel**: Shows exactly why you won (e.g., "Line 3: 3x Kings").
*   **Use Case**: Use this to debug. If you see 5 Wilds but no win, your code has a bug!

### 3. 📉 Deep Dive Analysis
The "Statistical Breakdown".
*   **Win Distribution**: A chart showing win sizes.
    *   *Tall bars on left*: Frequent small wins.
    *   *Bars on far right*: Rare jackpots.
*   **Reel Strips**: Visualizes the weight of every symbol. Helps you see if a symbol is too common or too rare.

### 4. 📜 PAR Sheet Export
*   A download button to get the Excel PAR sheet without using the command line.

---

## ❓ FAQ

**Q: The Dashboard shows 0% RTP or "No Data".**
A: You haven't run the simulation yet. Run: `python slot_math_engine/main.py simulate --spins 100000`

**Q: My Simulated RTP is 95% but Theoretical is 94.8%. Why?**
A: Variance. This is a high-volatility game (Std Dev > 60). It takes tens of millions of spins to converge perfectly. A +/- 0.6% deviation is normal for 5M spins.

**Q: How do I change the payouts?**
A: Edit `data/reel_configs/base_game.json`. Then run `analyze` and `simulate` again.
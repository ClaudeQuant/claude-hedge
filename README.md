![Claude Quant Banner](./images/github-banner.png)

# Claude Quant

[![Live Performance](https://img.shields.io/badge/Live_32_Days-+54%25-brightgreen)](./data/live_simulation_dec3_jan16.csv)
[![Backtest](https://img.shields.io/badge/Backtest_4_Years-+240%25_CAGR-blue)](./data/backtest_2021_2026.csv)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](./scripts/)
[![Pine Script](https://img.shields.io/badge/TradingView-Pine_Script-orange.svg)](./scripts/session_strategy.pine)

---

## The Princeton Anomaly

**In 2003, four Princeton graduate students discovered a systematic inefficiency in global futures markets. Twenty-one years later, one finally built it—powered by Claude AI.**

**AI discovered it. AI coded it. AI trades it.**

---

## 📊 **Verified Performance**

### Live Trading (32 Days)
- **Total Return:** +54.03%
- **Average Daily:** +1.69%
- **Win Rate:** 62.5%
- **Sharpe Ratio:** 3.2+

### Backtest (4 Years: 2021-2026)
- **CAGR:** 240%
- **Total Return:** +13,508% ($250K → $34M)
- **Sharpe Ratio:** 2.03
- **Max Drawdown:** -35.32%

**All data independently verifiable in `/data` folder.**

---

## 🤖 **The AI Implementation**

Claude AI analyzed the original 2003 Princeton thesis and:
1. **Extracted** the core time-zone arbitrage principle
2. **Coded** the complete trading framework
3. **Enhanced** it with modern VIX-adaptive risk management
4. **Deployed** it for autonomous trading

The result: A 21-year-old academic insight, now executed by AI.

---

## 🧠 **The System**

### Session Sequencing (Time-Zone Arbitrage)
- **Nikkei 225** (Asia) → **DAX** (Europe) → **Nasdaq** (US)
- Same capital traded 3x per day
- Zero overnight exposure

### VIX-Adaptive Risk Management
- Dynamic position sizing based on market volatility
- Scales down in crisis, scales up when calm

### Conditional Expansion
- Profitable Asia → Expanded Europe/US limits
- Asymmetric risk-taking

### Multi-Layer Protection
- Portfolio hard stops
- Per-market limits
- Session controls
- Automatic flattening

---

## 🔍 **Transparency & Verification**

### ✅ **Publicly Available:**
- Complete CSV performance data
- Python verification scripts
- TradingView Pine Script strategy
- Framework architecture code
- Comprehensive documentation

### ⚠️ **Proprietary:**
- Exact position sizing parameters
- Signal generation algorithms
- Conditional expansion values

**Don't trust. Verify.** Download and check yourself.

---

## 🚀 **Quick Start**

```bash
git clone https://github.com/ClaudeQuant/claude-quant.git
cd claude-quant
pip install pandas numpy matplotlib
python scripts/verify_performance.py
```

---

## 📈 **Performance Notes**

**Why 240% CAGR:**

Our backtest shows **240% Compound Annual Growth Rate (CAGR)** over 4 years. This is the geometric mean - the actual rate at which capital compounded.

**The Math:**
- Starting Capital: $250,000
- Ending Value: $34,019,317 (after 4.01 years)
- Total Return: +13,508%
- **CAGR: 240.12%**

Formula: (Ending/Starting)^(1/Years) - 1

**240% CAGR means doubling your money every 4.3 months on average.**

---

## 📚 **Documentation**

- [Methodology](./docs/methodology.md)
- [Risk Framework](./docs/risk_framework.md)
- [Results Analysis](./docs/results_analysis.md)
- [Roadmap](./docs/roadmap.md)

---

## 🎓 **Academic Foundation**

Built on a Princeton University thesis from 2003 exploring time-zone arbitrage. 21 years later, Claude AI has coded and deployed it with modern risk management.

---

## 📱 **Community**

- **Website:** https://claudequant.ai
- **X (Twitter):** @ClaudeQuant
- **Telegram:** [Coming Soon]

---

## ⚠️ **Disclaimer**

Trading futures involves substantial risk. **240% CAGR backtest** with **-35% max drawdown** demonstrates significant volatility. Past performance does not guarantee future results.

This is not investment advice.

---

**The most transparent AI trading project in cryptocurrency.**

**21 years of academic research. Claude AI execution. Complete transparency.**

**Don't trust. Verify.** 🔍

"""
About Page - Application information and documentation
"""

import streamlit as st
import sys
import os

# Add parent directory
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Page config
st.set_page_config(
    page_title="About",
    page_icon="ℹ️",
    layout="wide"
)

# Header
st.title("ℹ️ About AI Stock Analyst")
st.markdown("### Decentralized stock portfolio tracker powered by AI and blockchain")

st.divider()

# Overview
st.header("🌟 Overview")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **AI Stock Analyst** is a revolutionary financial analytics platform that combines:
    
    - 🤖 **Artificial Intelligence** for stock analysis
    - 🔗 **Blockchain Technology** for immutable record-keeping
    - 📊 **Real-time Data** from Yahoo Finance
    - 🔐 **Your Keys, Your Data** - non-custodial approach
    
    Built for investors, traders, and financial analysts who want:
    - Transparent portfolio tracking
    - AI-powered investment insights
    - Decentralized data ownership
    """)

with col2:
    st.image("https://img.icons8.com/clouds/400/000000/stocks.png", width=300)

st.divider()

# Features
st.header("✨ Key Features")

tab1, tab2, tab3 = st.tabs(["🤖 AI Analysis", "💼 Portfolio", "🔗 Blockchain"])

with tab1:
    st.subheader("AI-Powered Stock Analysis")
    st.markdown("""
    **Technical Indicators:**
    - **RSI (Relative Strength Index)**: Identifies overbought/oversold conditions
    - **MACD (Moving Average Convergence Divergence)**: Trend momentum indicator
    - **SMA (Simple Moving Averages)**: 20, 50, 200-day averages
    - **Bollinger Bands**: Volatility and price level analysis
    - **ATR (Average True Range)**: Volatility measurement
    
    **AI Recommendations:**
    - Buy/Hold/Sell signals based on multi-factor analysis
    - Confidence scoring (0-100%)
    - Detailed explanation of trading signals
    - Real-time data from Yahoo Finance
    
    **Supported Markets:**
    - 🇺🇸 US Stocks (NYSE, NASDAQ)
    - 🇮🇳 Indian Stocks (NSE)
    - 80+ major companies
    """)

with tab2:
    st.subheader("Portfolio Management")
    st.markdown("""
    **Track Your Investments:**
    - Add investments with company, shares, price, date
    - Real-time portfolio valuation
    - Gain/loss tracking with percentages
    - Historical purchase records
    
    **Storage Options:**
    - **Local Storage**: Temporary session storage
    - **Blockchain Storage**: Permanent Ethereum storage
    
    **Portfolio Analytics:**
    - Total invested amount
    - Current market value
    - Individual stock performance
    - Overall portfolio return (%)
    """)

with tab3:
    st.subheader("Blockchain Integration")
    st.markdown("""
    **Ethereum Smart Contract:**
    - **Network**: Sepolia Testnet
    - **Language**: Solidity 0.8.28
    - **Gas Optimized**: Efficient storage patterns
    
    **Features:**
    - Immutable investment records
    - Verifiable transaction history
    - Non-custodial (you control your keys)
    - Transparent and auditable
    
    **Contract Functions:**
    - `addInvestment()` - Store new investment
    - `getMyInvestments()` - Retrieve all investments
    - `removeInvestment()` - Mark as inactive
    - `getActiveInvestmentCount()` - Get portfolio size
    """)

st.divider()

# How it works
st.header("🔧 How It Works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 1️⃣ Stock Analysis
    
    ```
    User Input
       ↓
    Yahoo Finance API
       ↓
    Technical Indicators
       ↓
    AI Analysis Engine
       ↓
    Recommendation
    ```
    
    No wallet needed!
    """)

with col2:
    st.markdown("""
    ### 2️⃣ Portfolio Tracking
    
    ```
    Investment Details
       ↓
    Local/Blockchain Choice
       ↓
    Data Storage
       ↓
    Real-time Valuation
       ↓
    Portfolio Dashboard
    ```
    
    Flexible storage!
    """)

with col3:
    st.markdown("""
    ### 3️⃣ Blockchain Storage
    
    ```
    Wallet Connection
       ↓
    Transaction Creation
       ↓
    Gas Fee Payment
       ↓
    Smart Contract Call
       ↓
    Permanent Record
    ```
    
    Immutable storage!
    """)

st.divider()

# Technology stack
st.header("🛠️ Technology Stack")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Frontend:**
    - Streamlit 1.31.0
    - Python 3.9+
    - Plotly for visualizations
    
    **Backend:**
    - yfinance (stock data)
    - pandas (data processing)
    - numpy (calculations)
    - fuzzywuzzy (symbol lookup)
    """)

with col2:
    st.markdown("""
    **Blockchain:**
    - Solidity 0.8.28
    - Web3.py 7.4.0
    - eth-account 0.13.4
    - Ethereum Sepolia Testnet
    
    **Hosting:**
    - Streamlit Cloud
    - GitHub integration
    - Auto-deployment
    """)

st.divider()

# Contract info
st.header("📄 Smart Contract Details")

# Get contract address from secrets
contract_address = st.secrets.get("CONTRACT_ADDRESS", "Not configured")
rpc_url = st.secrets.get("RPC_URL", "Not configured")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **Contract Information:**
    - **Address**: `{contract_address}`
    - **Network**: Sepolia Testnet
    - **Chain ID**: 11155111
    - **Compiler**: Solidity 0.8.28
    - **License**: MIT
    """)

with col2:
    st.markdown(f"""
    **Links:**
    - [View on Etherscan](https://sepolia.etherscan.io/address/{contract_address})
    - [Sepolia Faucet](https://sepoliafaucet.com/)
    - [Alchemy Faucet](https://www.alchemy.com/faucets/ethereum-sepolia)
    - [GitHub Repository](https://github.com/Bhoomika M)
    """)

st.divider()

'''# Security
st.header("🔒 Security & Privacy")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Security Best Practices:**
    - ✅ Non-custodial (we never store your keys)
    - ✅ Testnet only (no real funds at risk)
    - ✅ Open source code
    - ✅ Verified smart contract
    - ✅ No data collection
    """)

with col2:
    st.markdown("""
    **Important Warnings:**
    - ⚠️ **NEVER** use mainnet private keys
    - ⚠️ This is testnet - no real money
    - ⚠️ Keep your private keys secure
    - ⚠️ We don't provide financial advice
    - ⚠️ DYOR (Do Your Own Research)
    """)

st.divider()'''

# FAQ
st.header("❓ Frequently Asked Questions")

with st.expander("Is this free to use?"):
    st.markdown("""
    Yes! The application is completely free. You only need:
    - Testnet ETH for blockchain transactions (free from faucets)
    - No subscription or fees
    """)

with st.expander("Is my money safe?"):
    st.markdown("""
    This application runs on Sepolia **TESTNET** only. Testnet ETH has no real value.
    Never use mainnet wallets or real funds with this application.
    """)

with st.expander("How do I get testnet ETH?"):
    st.markdown("""
    Visit these free faucets:
    - [Alchemy Sepolia Faucet](https://www.alchemy.com/faucets/ethereum-sepolia)
    - [Sepolia Faucet](https://sepoliafaucet.com/)
    - [Infura Faucet](https://www.infura.io/faucet/sepolia)
    
    You'll receive free testnet ETH (no value) for testing.
    """)

with st.expander("Can I use this for real trading?"):
    st.markdown("""
    **No!** This is an educational/demonstration tool only. 
    
    - It provides analysis but not financial advice
    - Runs on testnet (not real money)
    - Always DYOR (Do Your Own Research)
    - Consult financial advisors for real investments
    """)

with st.expander("How accurate are the AI recommendations?"):
    st.markdown("""
    AI recommendations are based on technical indicators only:
    - Historical price data
    - Volume analysis
    - Technical patterns
    
    **Not included:**
    - Fundamental analysis
    - News sentiment
    - Insider information
    - Market manipulation
    
    Use as one tool among many, not sole decision maker.
    """)

st.divider()

# Roadmap
st.header("🗺️ Roadmap")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Completed ✅**
    - Stock analysis with 5+ indicators
    - Portfolio tracking
    - Blockchain integration
    - Streamlit Cloud deployment
    - Multi-market support
    """)

with col2:
    st.markdown("""
    **Coming Soon 🚀**
    - More technical indicators
    - Chart visualizations
    - Price alerts
    - Multi-chain support
    - Mobile app
    """)

st.divider()

# Credits
st.header("👨‍💻 About the Developer")

st.markdown("""
**Bhoomika M**

- 🎓 Computer Science Student, Tamil Nadu, India
- 💻 Blockchain Developer & Data Scientist
- 🏀 Basketball Athlete
- 🔧 Tech Stack: Python, Solidity, JavaScript, C

**Connect:**
- GitHub: [@Bhoomika M](https://github.com/Bhoomika M)
- Portfolio: [View Projects](https://github.com/Bhoomika M)

**This Project:**
- Version: 1.0.0
- Release: October 2025
- License: MIT
- Lines of Code: 2,500+
""")

st.divider()

# Footer
st.markdown("""
---
<div style='text-align: center'>
    <h3>🚀 AI Stock Analyst with Blockchain</h3>
    <p>Built with ❤️ using Streamlit, Web3.py, yfinance, and Ethereum</p>
    <p><strong>© 2025 Bhoomika M | MIT License</strong></p>
    <p>
        <a href="https://github.com/Bhoomika M" target="_blank">GitHub</a> • 
        <a href="https://streamlit.io" target="_blank">Streamlit</a> • 
        <a href="https://ethereum.org" target="_blank">Ethereum</a>
    </p>
</div>
""", unsafe_allow_html=True)

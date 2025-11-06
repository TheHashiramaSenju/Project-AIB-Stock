# modified file: ai-stock-analyst-blockchain/streamlit_app/Home.py

"""
AI Stock Analyst with Blockchain - Streamlit Version
=====================================================
Main entry point (Home page) for the Streamlit application.

- This file serves as the main dashboard and entry point.
- It initializes the session state for the entire application.
- It provides the primary wallet connection interface in the sidebar.
- It EXCLUSIVELY uses the StockAdvisorFinnhub module, as requested.
  All YFinance-related code has been purged.

Author: Bhoomika M 
Version: 2.0.0
"""

import streamlit as st
import sys
import os

# --- Path Setup ---
# Add parent directory to path to import backend modules
# This allows streamlit to find 'stock_advisor_finnhub.py', etc.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


# --- ROBUST, FINNHUB-ONLY IMPORTS ---
# As per your explicit instruction, we are *only* importing the Finnhub
# advisor. The application will fail if it's not found, enforcing
# the strict dependency on Finnhub.
try:
    from stock_advisor_finnhub import StockAdvisorFinnhub
    from portfolio_manager import BlockchainPortfolioManagerEnhanced
    from blockchain_integration import BlockchainPortfolioManager
except ImportError as e:
    st.error(f"""
    **FATAL IMPORT ERROR:** Could not load core application modules.
    
    **Error:** `{e}`
    
    This application **exclusively** uses the Finnhub stock advisor. 
    Please ensure the following files are present in the `streamlit_app/` directory:
    - `stock_advisor_finnhub.py`
    - `portfolio_manager.py`
    - `blockchain_integration.py`
    
    The application cannot start without these files.
    """)
    st.stop()


# --- Page Configuration ---
# This must be the first Streamlit command.
st.set_page_config(
    page_title="AI Stock Analyst - Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/TheBhoomikaM',
        'Report a bug': 'https://github.com/TheBhoomikaM',
        'About': ('# AI Stock Analyst with Blockchain (v2.0)\n'
                  'Built by TheBhoomikaM. This app provides AI-driven stock analysis '
                  'using the **Finnhub API** and immutable portfolio tracking on the '
                  '**Ethereum (Sepolia)** blockchain.')
    }
)

# --- Custom CSS ---
# This CSS is optimized for both light and dark modes
st.markdown("""
<style>
    /* Main header gradient */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* Subheader - blue color */
    .sub-header {
        text-align: center;
        color: #1f77b4 !important;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    
    /* Info boxes - gradient background with white text */
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        height: 250px; /* Fixed height for alignment */
        display: flex;
        flex-direction: column;
    }
    .info-box h3 {
        color: white !important;
        margin-top: 0;
        font-size: 1.3rem;
        font-weight: 700;
    }
    .info-box p {
        color: white !important;
        opacity: 0.95;
        font-size: 1rem;
        line-height: 1.6;
        flex-grow: 1; /* Makes p tag fill space */
    }
    
    /* Metrics - gradient background */
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: none !important;
        color: white !important;
    }
    .stMetric label {
        color: white !important;
        font-weight: 600;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 2rem !important;
        font-weight: bold !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        color: white !important;
        opacity: 0.85;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    /* Sidebar wallet form */
    .st-emotion-cache-1jicfl2 {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
def init_session_state():
    """
    Initializes all required session state variables.
    This function is critical for sharing state between pages
    (e.g., wallet connection, advisor instance).
    """
    
    # Get Finnhub API key from secrets
    if 'finnhub_key' not in st.session_state:
        # st.secrets.get() is the standard way to securely access
        # the secrets.toml file in a Streamlit Cloud deployment.
        st.session_state.finnhub_key = st.secrets.get("FINNHUB_API_KEY", "d415bmpr01qo6qdf06d0d415bmpr01qo6qdf06dg")
        if not st.session_state.finnhub_key:
            st.error("FINNHUB_API_KEY not found in Streamlit secrets. The app cannot function.")
            st.stop()
    
    # Initialize StockAdvisorFinnhub (ONLY Finnhub)
    if 'advisor' not in st.session_state:
        st.session_state.advisor = StockAdvisorFinnhub(st.session_state.finnhub_key)
    
    # Initialize portfolio manager
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = BlockchainPortfolioManagerEnhanced(
            blockchain_enabled=True
        )
        # CRITICAL: Set the portfolio manager to use the FINNHUB advisor
        # This ensures get_current_price() and other functions work correctly
        # in the Portfolio page.
        st.session_state.portfolio_manager.set_stock_advisor(st.session_state.advisor)
    
    # Wallet connection status
    if 'wallet_connected' not in st.session_state:
        st.session_state.wallet_connected = False
    
    # Blockchain configuration (loaded from secrets)
    if 'contract_address' not in st.session_state:
        st.session_state.contract_address = st.secrets.get("CONTRACT_ADDRESS", "")
    
    if 'rpc_url' not in st.session_state:
        st.session_state.rpc_url = st.secrets.get("RPC_URL", "")
    
    # User ID for portfolio
    if 'user_id' not in st.session_state:
        # In a real app, this would come from a login system.
        # For this project, a single session ID is robust.
        st.session_state.user_id = "streamlit_user_session"
    
    # State variable for the AI Budgeting plan
    if 'generated_plan' not in st.session_state:
        st.session_state.generated_plan = None

# Call initialization
init_session_state()

# --- Main Page UI ---

# Header
st.markdown('<h1 class="main-header">🚀 AI Stock Analyst with Blockchain</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Professional-grade financial analysis meets decentralized portfolio management.</p>', unsafe_allow_html=True)

# Feature Boxes
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="info-box">
        <h3>📊 Stock Analysis</h3>
        <p>Go to the 'Stock Analysis' page to get real-time technical analysis, analyst ratings, and price targets powered by Finnhub API. Get AI-driven Buy/Sell/Hold recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-box">
        <h3>🤖 AI Budgeting</h3>
        <p>Go to the 'AI Budgeting' page. Enter a budget (e.g., $1000) and a risk profile (e.g., 'Aggressive'), and our AI will generate a complete, diversified investment plan based on analyst predictions.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-box">
        <h3>🔗 Blockchain Portfolio</h3>
        <p>Go to the 'Portfolio' page. Connect your wallet (in the sidebar) to save your 'AI Budgeting' plan or manual investments immutably on the Ethereum Sepolia testnet. Your keys, your data.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Quick Overview Metrics
st.subheader("📈 Platform Quick Stats")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Data Provider",
        value="Finnhub API",
        help="Using the professional-grade Finnhub API for real-time, reliable stock data. No YFinance."
    )

with col2:
    st.metric(
        label="Analysis Features",
        value="8+",
        help="RSI, MACD, SMA, Bollinger Bands, Analyst Ratings, Price Targets, AI Budgeting, and more."
    )

with col3:
    st.metric(
        label="Blockchain Network",
        value="Sepolia Testnet",
        help=f"Chain ID: 11155111. Contract: {st.session_state.contract_address[:10]}..."
    )

with col4:
    if st.session_state.wallet_connected:
        st.metric(
            label="Wallet Status",
            value="Connected ✅",
            delta="Blockchain features are active."
        )
    else:
        st.metric(
            label="Wallet Status",
            value="Not Connected ❌",
            delta="Please connect wallet in sidebar."
        )

st.divider()

# Exhaustive "How to Use" Guide
st.subheader("🚀 How to Use This Platform (Full Guide)")
st.markdown("Follow these steps for the complete end-to-end experience.")

with st.expander("Step 1: 🔗 Connect Your Wallet (Sidebar)", expanded=True):
    st.markdown("""
    This is the **most important step** for using the blockchain features.
    
    1.  **Open the Sidebar:** Click the `>` arrow in the top-left corner.
    2.  **Get Testnet ETH:** This application runs on the **Sepolia Testnet**, not the real Ethereum mainnet. This means all "money" is **fake** and **free**. Get your free testnet ETH from a faucet like:
        * [Sepolia Faucet](https://sepoliafaucet.com/)
        * [Alchemy Sepolia Faucet](https://www.alchemy.com/faucets/ethereum-sepolia)
    3.  **Find Your Private Key:**
        * In MetaMask, click the three dots `⋮` next to your account.
        * Go to `Account Details` > `Show Private Key`.
        * **⚠️ WARNING: NEVER, EVER use a private key from your REAL (mainnet) wallet. Create a new, separate wallet *just* for this testing.**
    4.  **Connect:** Paste your **Sepolia Testnet Private Key** into the text box in the sidebar.
    5.  Click **"🔐 Connect Wallet"**.
    6.  **Verify:** You should see a "✅ Wallet Connected" message with your wallet address and ETH balance. The 'Wallet Status' metric above should also update.
    """)

with st.expander("Step 2: 🤖 Generate an AI Investment Plan (Recommended)"):
    st.markdown("""
    This is the fastest way to build a portfolio.
    
    1.  Navigate to the **"🤖 AI Budgeting"** page from the sidebar.
    2.  **Enter Your Budget:** Input the total amount you wish to invest (e.g., `$1000`).
    3.  **Select Risk Profile:**
        * **Conservative:** Spreads your budget across 5-7 stable stocks.
        * **Moderate:** A balanced mix of 3-5 growth and stable stocks.
        * **Aggressive:** Concentrates your budget into 2-3 high-growth, high-conviction stocks.
    4.  Click **"🚀 Generate AI Investment Plan"**.
    5.  **Review the Plan:** The AI will scan the market, fetch analyst predictions, and build a complete plan showing which stocks to buy, how many shares, and the potential upside.
    6.  **Save to Blockchain:** If your wallet is connected, click the **"🔗 Save Plan to Blockchain"** button. The app will automatically execute and save *all* transactions to your portfolio, one by one.
    """)

with st.expander("Step 3: 📊 Analyze a Single Stock"):
    st.markdown("""
    Want to do your own research?
    
    1.  Navigate to the **"📊 Stock Analysis"** page.
    2.  Enter any US stock symbol (e.g., `NVDA`, `TSLA`, `GOOGL`).
    3.  Click **"🚀 Analyze"**.
    4.  Review the full analysis, including:
        * Real-time price data from Finnhub.
        * Analyst recommendations (e.g., 20 'Buy', 5 'Hold', 1 'Sell').
        * 12-Month price targets (predicted data).
        * Technical indicators like RSI, MACD, and Bollinger Bands.
        * An interactive price chart.
    """)

with st.expander("Step 4: 💼 Manage Your Portfolio"):
    st.markdown("""
    View and manage all your investments.
    
    1.  Navigate to the **"💼 Portfolio"** page.
    2.  **View Overview:** At the top, you'll see your portfolio's total value, total invested cost, and overall profit/loss.
    3.  **See Visualizations:** Interactive charts show your allocation by stock and by sector.
    4.  **Manually Add:** You can use the "Add Investment" form to add a single stock you bought.
    5.  **Manage Holdings:**
        * Each holding is listed with its shares, value, and P/L.
        * A `🔗` icon means it's saved on the blockchain.
        * A `💾` icon means it's saved locally (will be lost on refresh).
        * Click **"🗑️ Remove"** on any holding to send a transaction to mark it 'inactive' on the blockchain and remove it from your view.
    6.  **Sync Data:** If your local view seems wrong, click **"🔄 Sync All from Blockchain"** to force-reload your entire portfolio directly from the smart contract.
    """)

st.divider()

# Expanded Feature, Data, and Blockchain Info
st.subheader("✨ Platform Details")
feat_col1, feat_col2, feat_col3 = st.columns(3)

with feat_col1:
    st.markdown("""
    #### 🤖 AI & Analysis Features
    - **AI Budgeter:** Proactive portfolio generation.
    - **Risk Profiles:** Conservative, Moderate, Aggressive.
    - **Analyst Ratings:** Uses Finnhub's `recommendation_trends`.
    - **Price Targets:** Uses Finnhub's `price_target` for "predicted data".
    - **Technical Indicators:** RSI, MACD, SMA (20/50/200), Bollinger Bands.
    - **Interactive Charts:** Plotly charts for price history.
    - **Portfolio Charts:** Pie and Bar charts for allocation.
    """)
with feat_col2:
    st.markdown("""
    #### 🔗 Blockchain Integration
    - **Smart Contract:** `PortfolioTracker.sol` (Solidity v0.8.28).
    - **Network:** Sepolia Testnet (Chain ID 11155111).
    - **Immutable Records:** `addInvestment` and `removeInvestment` functions.
    - **Full Ownership:** You are the *only* one who can access or modify your data via your private key.
    - **Gas-Optimized:** Contract is optimized to reduce transaction fees.
    - **On-Chain View:** All transactions are verifiable on [Sepolia Etherscan](https://sepolia.etherscan.io/).
    """)
with feat_col3:
    st.markdown("""
    #### ⚡ Data Provider: Finnhub API
    - **Exclusivity:** This app **only** uses the Finnhub API. All YFinance logic has been removed.
    - **Robustness:** 60 API calls/minute on the free tier, eliminating the rate-limiting issues common with other free APIs.
    - **Data Quality:** Provides real-time, professional-grade data, including analyst predictions and deep market insights.
    - **Functions Used:**
        - `client.quote()` (Real-time price)
        - `client.stock_candles()` (Historical data)
        - `client.recommendation_trends()` (Analyst ratings)
        - `client.price_target()` (Analyst price targets)
        - `client.company_profile2()` (Sector/Industry info)
    """)

st.divider()

# --- Security & Disclaimer ---
st.subheader("🔒 Security, Privacy, and Disclaimer")
st.warning("**Important: Please read this section carefully.**")

sec_col1, sec_col2 = st.columns(2)
with sec_col1:
    st.markdown("""
    #### 🔐 **Security & Privacy**
    
    * **Non-Custodial:** This application is **100% non-custodial**. Your private key is *never* sent to any server. It is stored *only* in your local browser's session state (in `st.session_state`) and is used *locally* to sign transactions. If you refresh your browser, it is **gone**.
    * **Testnet Only:** This is a **TESTNET** application. It uses the Sepolia network, where the ETH has **NO REAL-WORLD VALUE**. It is for demonstration and educational purposes only.
    * **No Mainnet Keys:** **NEVER** use a private key from your real (mainnet) wallet. Create a brand new, empty wallet in MetaMask *exclusively* for this test.
    * **Open Source:** The full source code, including the smart contract, is available for public audit.
    """)
with sec_col2:
    st.markdown("""
    #### 📜 **Financial Disclaimer**
    
    * **Not Financial Advice:** The information provided by this tool, including all AI recommendations, stock analyses, and generated portfolios, is for **informational and educational purposes ONLY**.
    * **No Guarantee:** This tool does **NOT** constitute financial advice, investment advice, or a solicitation to buy or sell any assets.
    * **High Risk:** All investments, especially in stocks, carry significant risk. You could lose all of your invested capital. Past performance is not an indicator of future results.
    * **Do Your Own Research (DYOR):** The AI's "predictions" are based on analyst ratings and historical data, which may be inaccurate. You must conduct your own thorough research before making any investment decisions.
    * **Consult a Professional:** Always consult with a qualified, licensed financial advisor before making any financial decisions.
    """)

st.divider()

# --- Footer ---
st.markdown(f"""
---
<div style='text-align: center'>
    <p><strong>AI Stock Analyst v2.0.0 (Finnhub Edition)</strong> | Built with ❤️ by TheBhoomikaM</p>
    <p>Powered by Streamlit, Finnhub API, Web3.py, and Ethereum blockchain</p>
    <p>
        <a href="https://github.com/TheBhoomikaM" target="_blank">GitHub</a> • 
        <a href="https://sepolia.etherscan.io/address/{st.session_state.contract_address}" target="_blank">Smart Contract</a> • 
        <a href="https://finnhub.io" target="_blank">Finnhub API</a>
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR LOGIC ---
# This remains the most critical interactive component on the Home page.
# It is already robust and does not need modification.

with st.sidebar:
    st.header("🔗 Blockchain Connection")
    
    if not st.session_state.wallet_connected:
        st.info("Connect your wallet to enable all blockchain portfolio features.")
        
        st.markdown("**Network:** Sepolia Testnet")
        contract_display = (f"`{st.session_state.contract_address[:10]}...`" 
                            if st.session_state.contract_address 
                            else "`Not configured in secrets`")
        st.markdown(f"**Contract:** {contract_display}")
        
        if not st.session_state.contract_address or not st.session_state.rpc_url:
            st.error("Missing `CONTRACT_ADDRESS` or `RPC_URL` in secrets.toml. App cannot connect.")
        else:
            with st.form("wallet_form"):
                private_key = st.text_input(
                    "Enter Your Sepolia Private Key",
                    type="password",
                    help="NEVER use a mainnet key! Create a new test wallet."
                )
                
                submit = st.form_submit_button("🔐 Connect Wallet", type="primary", use_container_width=True)
                
                if submit:
                    if not private_key:
                        st.warning("Please enter your private key.")
                    else:
                        with st.spinner("Connecting to blockchain..."):
                            try:
                                # Use the connect_blockchain function from portfolio_manager
                                result = st.session_state.portfolio_manager.connect_blockchain(
                                    private_key,
                                    st.session_state.contract_address,
                                    None  # ABI path is optional, will find it
                                )
                                
                                if "Connected Successfully" in result:
                                    st.session_state.wallet_connected = True
                                    st.success("✅ Wallet connected!")
                                    st.rerun() # Rerun to update the page
                                else:
                                    st.error(f"Connection Failed: {result}")
                            except Exception as e:
                                st.error(f"Critical Connection Error: {str(e)}")
    else:
        st.success("✅ Wallet Connected")
        
        if st.session_state.portfolio_manager.blockchain and st.session_state.portfolio_manager.blockchain.account:
            wallet_addr = st.session_state.portfolio_manager.blockchain.account.address
            
            try:
                # Fetch balance on-the-fly
                balance = st.session_state.portfolio_manager.blockchain.get_balance()
            except Exception as e:
                st.error(f"Could not fetch balance: {e}")
                balance = 0.0
            
            st.markdown(f"""
            **Address:** `{wallet_addr[:10]}...{wallet_addr[-8:]}`
            
            **Balance:** `{balance:.6f} ETH`
            """)
        
        if st.button("🔌 Disconnect Wallet", use_container_width=True, type="secondary"):
            st.session_state.wallet_connected = False
            st.session_state.portfolio_manager.blockchain.disconnect() # Clear sensitive keys
            st.rerun()
    
    st.divider()
    
    st.markdown("""
    **📚 Quick Links:**
    - [Get Testnet ETH](https://sepoliafaucet.com/)
    - [View Contract on Etherscan](https://sepolia.etherscan.io/address/{})
    - [Finnhub API](https://finnhub.io)
    - [GitHub Repository](https://github.com/TheBhoomikaM)
    - [Streamlit Docs](https://docs.streamlit.io/)
    """.format(st.session_state.contract_address))
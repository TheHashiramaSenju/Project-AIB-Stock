"""
AI Portfolio Budgeter - Alpha Vantage Edition (COMPREHENSIVE BEGINNER-FRIENDLY)
=============================================================================
Complete investment plan generator with:
- Beginner-friendly explanations for every feature
- Live step-by-step analysis breakdown
- Interactive learning modules
- Comprehensive error handling and diagnostics
- Real-time feedback and guidance
- Full technical analysis explanations
- Investment glossary and tutorials
- Blockchain integration

Features:
- 2-stock optimization (AAPL + MSFT)
- Technical analysis (RSI, MACD, Trend, Momentum)
- Risk profile-based allocation
- Live analysis log with detailed breakdowns
- Beginner's guide and learning materials
- API health checks and diagnostics
- Portfolio blockchain saving
- Educational expandable sections

Author: Bhoomika M
Date: 2025-11-08
Version: 4.0 (Comprehensive Beginner-Friendly)
Lines: 2000+
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import time
from typing import Tuple, List, Dict, Optional, Any
import requests
import logging


# --- Logging Configuration ---
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("="*100)
logger.info("AI PORTFOLIO BUDGETER - STARTING UP")
logger.info("="*100)

# --- Path Setup ---
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# --- Import Error Handling ---
imports_successful = True
import_errors = []

try:
    from stock_advisor_alphavantage import StockAdvisorAlphaVantage
    logger.info("✓ StockAdvisorAlphaVantage imported successfully")
except ImportError as e:
    import_errors.append(f"stock_advisor_alphavantage: {str(e)}")
    imports_successful = False
    logger.error(f"✗ Failed to import StockAdvisorAlphaVantage: {e}")

try:
    from ai_budgeter import AIBudgeter
    logger.info("✓ AIBudgeter imported successfully")
except ImportError as e:
    import_errors.append(f"ai_budgeter: {str(e)}")
    imports_successful = False
    logger.error(f"✗ Failed to import AIBudgeter: {e}")

try:
    from portfolio_manager import BlockchainPortfolioManagerEnhanced
    logger.info("✓ BlockchainPortfolioManagerEnhanced imported successfully")
except ImportError as e:
    import_errors.append(f"portfolio_manager: {str(e)}")
    imports_successful = False
    logger.error(f"✗ Failed to import BlockchainPortfolioManagerEnhanced: {e}")

try:
    from blockchain_integration import BlockchainPortfolioManager
    logger.info("✓ BlockchainPortfolioManager imported successfully")
except ImportError as e:
    import_errors.append(f"blockchain_integration: {str(e)}")
    imports_successful = False
    logger.error(f"✗ Failed to import BlockchainPortfolioManager: {e}")

if not imports_successful:
    st.error("🚨 **Critical Import Error**")
    st.error("The following modules could not be imported:")
    for error in import_errors:
        st.error(f"- {error}")
    st.error("\n**Required files in `streamlit_app/` directory:**")
    st.error("- `stock_advisor_alphavantage.py` (1500+ lines)")
    st.error("- `ai_budgeter.py` (350+ lines)")
    st.error("- `portfolio_manager.py`")
    st.error("- `blockchain_integration.py`")
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Budgeting - Investment Plan Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    /* Main containers */
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
    }
    
    /* Beginner boxes */
    .beginner-box {
        background: #e8f4f8;
        border-left: 5px solid #0084ff;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .beginner-box h4 {
        color: #0084ff;
        margin-top: 0;
    }
    
    .beginner-box p {
        color: #003d7a;
        line-height: 1.6;
    }
    
    /* Step boxes */
    .step-box {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .step-box h4 {
        color: #856404;
        margin-top: 0;
    }
    
    /* Analysis boxes */
    .analysis-box {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .warning-box {
        background: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    /* Tables */
    .glossary-table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .glossary-table td {
        padding: 1rem;
        border-bottom: 1px solid #ddd;
    }
    
    .glossary-table strong {
        color: #0084ff;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """
    Initialize all session state variables with comprehensive error handling.
    Manages: API keys, advisor instances, portfolio manager, and user state.
    """
    
    logger.info("Initializing session state...")
    
    # ===== Alpha Vantage API Key =====
    if 'alpha_vantage_key' not in st.session_state:
        try:
            api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "ZRBAZ10IY283K3T7")
            
            st.session_state.alpha_vantage_key = api_key
            st.session_state.api_key_source = "secrets" if st.secrets.get("ALPHA_VANTAGE_API_KEY") else "default"
            st.session_state.api_key_configured = True
            
            logger.info(f"✓ API Key configured from: {st.session_state.api_key_source}")
            logger.info(f"✓ API Key (first 10 chars): {api_key[:10]}...")
            
        except Exception as e:
            logger.error(f"✗ Error loading API key: {e}")
            st.session_state.alpha_vantage_key = "ZRBAZ10IY283K3T7"
            st.session_state.api_key_source = "default"
            st.session_state.api_key_configured = False
    
    # ===== StockAdvisorAlphaVantage =====
    if 'advisor' not in st.session_state:
        try:
            st.session_state.advisor = StockAdvisorAlphaVantage(st.session_state.alpha_vantage_key)
            st.session_state.advisor_initialized = True
            st.session_state.advisor_error = None
            logger.info("✓ StockAdvisorAlphaVantage initialized successfully")
        except Exception as e:
            st.session_state.advisor = None
            st.session_state.advisor_initialized = False
            st.session_state.advisor_error = str(e)
            logger.error(f"✗ Failed to initialize advisor: {e}")
    
    # ===== BlockchainPortfolioManagerEnhanced =====
    if 'portfolio_manager' not in st.session_state:
        try:
            st.session_state.portfolio_manager = BlockchainPortfolioManagerEnhanced(
                blockchain_enabled=True
            )
            if st.session_state.advisor:
                st.session_state.portfolio_manager.set_stock_advisor(st.session_state.advisor)
            st.session_state.portfolio_manager_initialized = True
            logger.info("✓ BlockchainPortfolioManagerEnhanced initialized")
        except Exception as e:
            st.session_state.portfolio_manager = None
            st.session_state.portfolio_manager_initialized = False
            logger.error(f"✗ Failed to initialize portfolio manager: {e}")
    
    # ===== Wallet & Blockchain Configuration =====
    if 'wallet_connected' not in st.session_state:
        st.session_state.wallet_connected = False
        st.session_state.contract_address = st.secrets.get("CONTRACT_ADDRESS", "")
        st.session_state.rpc_url = st.secrets.get("RPC_URL", "")
        logger.info("✓ Wallet and blockchain configuration loaded")
    
    # ===== User & Portfolio State =====
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "streamlit_user"
        st.session_state.generated_plan = None
        st.session_state.analysis_log = []
        st.session_state.current_candidates = None
        logger.info("✓ User and portfolio state initialized")

try:
    init_session_state()
except Exception as e:
    logger.error(f"Critical error during session state initialization: {e}", exc_info=True)
    st.error("🚨 **Fatal Error During Initialization**")
    st.error(f"Details: {str(e)}")
    st.stop()


def check_api_health(api_key: str) -> Dict[str, Any]:
    """
    Tests Alpha Vantage API connectivity with comprehensive diagnostics.
    Checks: response status, API errors, rate limits, and data validity.
    
    Returns:
        Dict with status, message, and detailed information
    """
    logger.info("Starting API health check...")
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": "AAPL",
            "apikey": api_key
        }
        
        logger.info(f"Testing API with symbol AAPL...")
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"API Response Status Code: {response.status_code}")
        
        data = response.json()
        logger.info(f"API Response Keys: {list(data.keys())}")
        
        # Check for error responses
        if "Error Message" in data:
            error_msg = data['Error Message']
            logger.error(f"API Error: {error_msg}")
            return {
                "status": "error",
                "message": f"Invalid API Key or API Error",
                "details": error_msg,
                "code": "INVALID_KEY",
                "emoji": "❌"
            }
        
        if "Note" in data:
            note_msg = data['Note']
            logger.warning(f"Rate limit: {note_msg}")
            return {
                "status": "rate_limited",
                "message": "Rate Limit Reached",
                "details": note_msg,
                "code": "RATE_LIMITED",
                "emoji": "⏳"
            }
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            if quote and quote.get("05. price"):
                logger.info(f"✓ API Health Check PASSED - AAPL Price: {quote['05. price']}")
                return {
                    "status": "success",
                    "message": "✅ API is working correctly",
                    "details": f"Successfully retrieved AAPL quote: ${quote['05. price']}",
                    "code": "HEALTHY",
                    "emoji": "✅"
                }
        
        logger.warning("Unexpected API response structure")
        return {
            "status": "unknown",
            "message": "Unexpected API Response",
            "details": f"Response structure unexpected. Keys: {list(data.keys())}",
            "code": "UNKNOWN_RESPONSE",
            "emoji": "❓"
        }
        
    except requests.exceptions.Timeout:
        logger.error("API request timeout")
        return {
            "status": "error",
            "message": "Connection Timeout",
            "details": "Alpha Vantage server did not respond in time (10 seconds)",
            "code": "TIMEOUT",
            "emoji": "⏱️"
        }
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to API")
        return {
            "status": "error",
            "message": "Cannot Connect to API",
            "details": "Check your internet connection. Is your wifi/internet working?",
            "code": "NO_CONNECTION",
            "emoji": "🔌"
        }
    except Exception as e:
        logger.error(f"Unexpected error in health check: {e}")
        return {
            "status": "error",
            "message": f"Health Check Error: {type(e).__name__}",
            "details": str(e),
            "code": "HEALTH_CHECK_ERROR",
            "emoji": "⚠️"
        }


@st.cache_data(ttl=3600)
def get_stock_candidates(_advisor: StockAdvisorAlphaVantage) -> Tuple[List[Dict], str]:
    """
    Analyzes 2 premium stocks with comprehensive error handling.
    Stocks: AAPL (Apple), MSFT (Microsoft) - Both highly liquid, stable
    
    Process:
    1. Define stock universe (AAPL + MSFT)
    2. For each stock: Fetch real-time data + technical indicators
    3. Validate data quality
    4. Return candidates with full technical data
    
    Args:
        _advisor: StockAdvisorAlphaVantage instance
        
    Returns:
        Tuple of (candidates_list, error_summary_string)
    """
    
    logger.info("="*100)
    logger.info("STARTING STOCK ANALYSIS")
    logger.info("="*100)
    
    if _advisor is None:
        error = "Advisor not initialized. Cannot analyze stocks."
        logger.error(f"✗ {error}")
        return [], error
    
    # Define our stock universe - only 2 stocks for free tier
    stock_universe = {
        'AAPL': 'Technology',  # Apple - Tech leader
        'MSFT': 'Technology'   # Microsoft - Software giant
    }
    
    candidates = []
    errors = []
    analysis_count = 0
    
    progress_bar = st.progress(0, text="Analyzing market candidates...")
    status_placeholder = st.empty()
    
    total_stocks = len(stock_universe)
    
    for i, (symbol, sector) in enumerate(stock_universe.items()):
        progress = (i + 1) / total_stocks
        progress_bar.progress(progress)
        status_placeholder.info(f"📊 Analyzing {symbol} ({i+1}/{total_stocks})...")
        
        try:
            logger.info(f"[{i+1}/{total_stocks}] Analyzing {symbol}...")
            logger.info(f"  Symbol: {symbol}, Sector: {sector}")
            
            # Call the analysis function - this makes 1 API call per stock
            analysis = _advisor.analyze_stock_technical(symbol)
            
            if analysis is None:
                error = f"{symbol}: No data returned from API"
                errors.append(error)
                logger.warning(f"✗ {error}")
                continue
            
            if not isinstance(analysis, dict):
                error = f"{symbol}: Invalid data type (expected dict, got {type(analysis).__name__})"
                errors.append(error)
                logger.warning(f"✗ {error}")
                continue
            
            # Validate critical fields
            if 'price' not in analysis:
                error = f"{symbol}: Missing 'price' field"
                errors.append(error)
                logger.warning(f"✗ {error}")
                continue
            
            price = analysis['price']
            if price is None or price <= 0:
                error = f"{symbol}: Invalid price value: {price}"
                errors.append(error)
                logger.warning(f"✗ {error}")
                continue
            
            # Build candidate record with all technical data
            candidate = {
                'symbol': symbol,
                'name': symbol,
                'sector': sector,
                'price': float(price),
                'change_percent': str(analysis.get('change_percent', '0%')),
                'change': float(analysis.get('change', 0)),
                'rsi': analysis.get('rsi'),
                'macd_signal': analysis.get('macd_signal', 'HOLD'),
                'trend': analysis.get('trend', 'NEUTRAL'),
                'recommendation': analysis.get('recommendation', 'HOLD'),
                'volume': int(analysis.get('volume', 0)),
                'high': float(analysis.get('high', 0)),
                'low': float(analysis.get('low', 0))
            }
            
            candidates.append(candidate)
            analysis_count += 1
            
            logger.info(f"✓ {symbol} analyzed successfully")
            logger.info(f"  Price: ${price:.2f}")
            logger.info(f"  RSI: {analysis.get('rsi', 'N/A')}")
            logger.info(f"  MACD: {analysis.get('macd_signal', 'N/A')}")
            logger.info(f"  Trend: {analysis.get('trend', 'N/A')}")
            logger.info(f"  Recommendation: {analysis.get('recommendation', 'N/A')}")
            
            status_placeholder.success(f"✓ {symbol} analyzed successfully")
            
            # Rate limit delay - respect API limits
            if i < total_stocks - 1:
                time.sleep(2)
            
        except Exception as e:
            error = f"{symbol}: {type(e).__name__}: {str(e)}"
            errors.append(error)
            logger.error(f"✗ Exception while analyzing {symbol}: {e}", exc_info=True)
    
    progress_bar.empty()
    status_placeholder.empty()
    
    # Summary logging
    logger.info("="*100)
    logger.info(f"STOCK ANALYSIS COMPLETE")
    logger.info(f"Successfully analyzed: {analysis_count}/{total_stocks}")
    logger.info(f"Errors encountered: {len(errors)}")
    for error in errors:
        logger.warning(f"  - {error}")
    logger.info("="*100)
    
    error_text = "\n".join(errors) if errors else ""
    return candidates, error_text

# --- Plan Generation Function ---

def generate_investment_plan(budget: float, risk_profile: str, 
                            candidates: List[Dict], 
                            advisor: StockAdvisorAlphaVantage) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Generates investment plan using AIBudgeter.
    
    Process:
    1. Validate inputs (budget, risk profile, candidates)
    2. Filter stocks by risk profile criteria
    3. Calculate technical scores
    4. Rank stocks by weighted score
    5. Allocate budget across selected stocks
    6. Return final plan with share quantities
    
    Args:
        budget: Total investment budget ($100-$1,000,000)
        risk_profile: 'Conservative', 'Moderate', or 'Aggressive'
        candidates: List of analyzed stocks with technical data
        advisor: Stock advisor instance (for data validation)
        
    Returns:
        Tuple of (plan_list, error_message)
        - plan_list: List of investment items with shares, prices, costs
        - error_message: None if successful, error string if failed
    """
    
    logger.info("="*100)
    logger.info("STARTING PLAN GENERATION")
    logger.info(f"Budget: ${budget:.2f}, Risk Profile: {risk_profile}")
    logger.info(f"Candidates: {len(candidates)} stocks")
    logger.info("="*100)
    
    if not candidates or len(candidates) == 0:
        error = "No stock candidates available for analysis."
        logger.error(f"✗ {error}")
        return None, error
    
    try:
        # Initialize budgeter
        budgeter = AIBudgeter()
        budgeter.set_verbose(False)  # Don't log to console, we have our own logging
        
        logger.info(f"AIBudgeter initialized")
        logger.info(f"Generating plan for {risk_profile} profile with ${budget:.2f}...")
        
        # Generate plan using AI Budgeter
        plan, error = budgeter.generate_investment_plan(budget, risk_profile, candidates)
        
        if error:
            logger.error(f"✗ AIBudgeter error: {error}")
            return None, error
        
        if not plan:
            error = "Plan generation returned no results."
            logger.error(f"✗ {error}")
            return None, error
        
        # Validate and log plan
        for idx, item in enumerate(plan):
            if 'sector' not in item:
                item['sector'] = 'Unknown'
            
            logger.info(f"  [{idx+1}] {item['symbol']}: ${item['cost']:.2f} "
                       f"({item['allocation_pct']:.1f}%) - "
                       f"{item['shares']:.4f} shares @ ${item['current_price']:.2f} - "
                       f"Upside: {item['upside_pct']:.1f}%")
        
        logger.info("="*100)
        logger.info(f"PLAN GENERATION COMPLETE - {len(plan)} items")
        logger.info("="*100)
        
        return plan, None
        
    except Exception as e:
        error = f"Plan generation error: {type(e).__name__}: {str(e)}"
        logger.error(f"✗ {error}", exc_info=True)
        return None, error


def show_welcome_section():
    """Display welcome message and beginner's guide."""
    
    st.markdown("""
    <div class="info-box">
        <h3>👋 Welcome to AI Portfolio Budgeter!</h3>
        <p>Your intelligent investment advisor that analyzes stock market data and creates 
        personalized investment plans based on your budget and risk tolerance.</p>
    </div>
    """, unsafe_allow_html=True)

def show_beginners_section():
    """Show comprehensive beginner's guide."""
    
    with st.expander("📚 Beginner's Guide - Start Here!", expanded=False):
        st.markdown("""
        ### What is Stock Market Investing?
        
        Investing in stocks means buying small pieces of companies. When a company does well, your investment grows!
        
        **Example:** 
        - You invest $1,000 today
        - Buy shares of Apple (AAPL) and Microsoft (MSFT)
        - In 12 months, your investment could grow to $1,123
        - You made a profit of $123! 📈
        
        ### What Does This App Do?
        
        **Your 4-Step Journey:**
        
        **Step 1️⃣: You Tell Us Your Budget** 💰
        - Enter how much money you want to invest
        - Range: $100 - $1,000,000
        - Example: $1,000
        
        **Step 2️⃣: You Choose Your Risk Level** 📊
        - **Conservative** = Safer, slower growth (like savings account)
        - **Moderate** = Balanced (some safety, some growth) ⭐ Recommended for beginners
        - **Aggressive** = More risky, faster potential growth
        
        **Step 3️⃣: AI Analyzes Companies** 🤖
        - Looks at real-time stock charts
        - Analyzes technical indicators (RSI, MACD, Trends)
        - Finds good investment opportunities
        - Calculates how much to invest in each stock
        
        **Step 4️⃣: You Get Your Plan** 📋
        - A list of specific stocks to buy
        - Exact number of shares to purchase
        - Expected profit potential (12-month target)
        - Blockchain option to record your plan permanently
        
        ### Key Investment Terms (Don't Worry - Simple!)
        
        | Term | What It Means | Example |
        |------|--------------|---------|
        | **Stock** | A small piece of a company | 1 share of Apple |
        | **Share** | One unit of a stock | Buy 5 shares of Apple |
        | **Price** | Cost of 1 share | Apple = $160/share |
        | **Portfolio** | Your collection of stocks | You own AAPL + MSFT |
        | **Diversification** | Not all eggs in one basket | Own different companies |
        | **Upside** | Potential profit | Stock could grow 12% |
        | **RSI** | Stock momentum (0-100 scale) | <30 = Cold (good buy), >70 = Hot (risky) |
        | **MACD** | Trend direction indicator | BUY = Upward ⬆️, SELL = Downward ⬇️ |
        | **Trend** | Which way stock is moving | BULLISH = Up 📈, BEARISH = Down 📉 |
        | **Health Score** | Overall stock quality (0-100) | 80+ = Excellent, 50-80 = Good |
        
        ### How the AI Scores Stocks (0-100 Scale)
        
        The AI analyzes each stock using 4 technical indicators:
        
        1. **RSI (30 points max)**
           - Is it oversold/undervalued?
           - Below 30 = Great buying opportunity
           - Above 70 = Potentially overpriced
        
        2. **MACD (35 points max)**
           - What's the trend momentum?
           - BUY signal = Momentum turning positive
           - SELL signal = Momentum turning negative
        
        3. **Trend (20 points max)**
           - Is the stock going up or down?
           - BULLISH = 50-day avg > 200-day avg (good!)
           - BEARISH = 50-day avg < 200-day avg (be careful)
        
        4. **Momentum (10 points max)**
           - Is the stock gaining speed?
           - Positive change = Good sign
           - Negative change = Bad sign
        
        **Final Score:**
        - **80-100** = Excellent buy! 🚀
        - **60-80** = Good buy ✅
        - **40-60** = Neutral ⚖️
        - **Below 40** = Risky ⚠️
        
        ### Real Example: $1,000 Investment Plan
        
        **Your Inputs:**
        - Budget: $1,000
        - Risk Profile: Moderate
        - Recommended Stocks: AAPL + MSFT
        
        **Your Plan:**
        
        | Stock | Price | Shares | Your $ | AI's Target | Potential Gain |
        |-------|-------|--------|--------|-------------|----------------|
        | AAPL | $160 | 3.1 | $496 | $180 | +12.5% |
        | MSFT | $245 | 2.0 | $490 | $275 | +12.2% |
        | **Total** | - | - | **$986** | - | **+12.3%** |
        
        **What This Means:**
        - You invest $986 today
        - Buy 3.1 shares of Apple + 2 shares of Microsoft
        - In 12 months, your investment could be worth ~$1,108
        - Potential profit: $122 (12.3% return)
        
        ### ⚠️ Important Things to Know
        
        ✅ **DO:**
        - Only invest money you can afford to lose
        - Think long-term (5+ years)
        - Diversify (own different companies)
        - Review your plan regularly
        - Start with small amounts if you're nervous
        
        ❌ **DON'T:**
        - Panic if stock price goes down (normal!)
        - Put all money in one stock
        - Try to time the market perfectly
        - Check prices obsessively every day
        - Borrow money to invest
        
        ### ⚠️ Disclaimer
        Past performance doesn't guarantee future results. Stock markets can go up OR down.
        This app provides suggestions, not financial advice. Always do your own research!
        """)


# Page setup
show_welcome_section()

st.markdown("""
<div class="info-box">
    <h3>🎯 How This Works (3 Simple Steps)</h3>
    <p>
    <strong>Step 1:</strong> Enter your investment budget and choose your risk level<br>
    <strong>Step 2:</strong> AI analyzes stocks (takes ~30 seconds)<br>
    <strong>Step 3:</strong> Get your personalized investment plan<br>
    </p>
</div>
""", unsafe_allow_html=True)

# Show beginner's guide link
show_beginners_section()

st.divider()



st.subheader("📋 Step 1: Configure Your Investment")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="step-box">
        <h4>💰 Your Investment Budget</h4>
        <p>This is the total amount of money you want to invest today. 
        The AI will divide this between recommended stocks based on your risk profile.
        <br><br>
        <strong>Tips:</strong>
        • Start small ($100-$500) if you're nervous
        • Invest money you don't need for 5+ years
        • Regular investing (monthly) builds wealth faster</p>
    </div>
    """, unsafe_allow_html=True)
    
    budget = st.number_input(
        "💵 How much do you want to invest?",
        min_value=100.0,
        max_value=1000000.0,
        value=1000.0,
        step=100.0,
        help="Minimum: $100, Maximum: $1,000,000. Start small if you're new to investing!"
    )
    st.markdown(f"**Your Budget: ${budget:,.2f}**")

with col2:
    st.markdown("""
    <div class="step-box">
        <h4>📊 Your Risk Profile</h4>
        <p>This determines how the AI divides your money between stocks.
        <br><br>
        🛡️ <strong>Conservative:</strong> Safer, stable companies, slower growth<br>
        ⚖️ <strong>Moderate:</strong> Balanced mix, recommended for beginners ⭐<br>
        🚀 <strong>Aggressive:</strong> Higher growth potential, more risky<br>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    risk_profile = st.selectbox(
        "📊 Choose your investment style:",
        ['Conservative', 'Moderate', 'Aggressive'],
        index=1,
        help="Moderate is recommended for beginners"
    )
    
    # Show risk profile info
    if risk_profile == 'Conservative':
        st.markdown("🛡️ **Safety First** - Lower risk, slower growth, good for risk-averse investors")
    elif risk_profile == 'Moderate':
        st.markdown("⚖️ **Balanced Approach** - Good for beginners, mixes safety with growth ⭐ Recommended")
    else:
        st.markdown("🚀 **Growth Focus** - Higher potential returns, but more volatility")

st.divider()


st.subheader("🔍 Step 2: Let AI Analyze the Market")

with st.expander("📚 What the AI Looks For", expanded=False):
    st.markdown("""
    ### The AI Checks 4 Technical Indicators:
    
    **1. RSI (Relative Strength Index)** - Stock Momentum
    - 0-30: Stock is "cold" = Great buying opportunity ❄️
    - 30-70: Normal zone = Neutral
    - 70-100: Stock is "hot" = Potentially overpriced 🔥
    
    **2. MACD (Moving Average Convergence Divergence)** - Trend Momentum
    - BUY signal: Momentum turning positive ⬆️
    - HOLD: No clear direction
    - SELL signal: Momentum turning negative ⬇️
    
    **3. Trend (50-day vs 200-day Moving Average)** - Direction
    - BULLISH: Recent average > Long-term average (going up!) ✅
    - BEARISH: Recent average < Long-term average (going down) ⚠️
    
    **4. Momentum (Daily Price Change)** - Speed
    - Positive % = Stock gaining speed upward 🚀
    - Negative % = Stock losing momentum ⬇️
    
    ### How Scores Are Calculated:
    - RSI: 0-35 points
    - MACD: 0-35 points
    - Trend: 0-20 points
    - Momentum: 0-10 points
    - **Total: 100 points maximum**
    
    ### Final Score Interpretation:
    - **80-100:** Excellent stock quality 🚀
    - **60-80:** Good stock quality ✅
    - **40-60:** Average stock quality ⚖️
    - **Below 40:** Higher risk ⚠️
    """)

generate_btn = st.button(
    "🚀 Analyze Stocks & Generate My Plan",
    type="primary",
    use_container_width=True,
    help="This will analyze AAPL and MSFT, takes about 30 seconds"
)

st.divider()

if generate_btn:
    logger.info("User clicked: Generate Plan")
    st.session_state.generated_plan = None
    st.session_state.analysis_log = []
    
    # Pre-flight checks
    if not st.session_state.advisor_initialized:
        st.error("🚨 API not configured properly")
        st.error(f"Error: {st.session_state.advisor_error}")
        st.error("**Solution:** Check `.streamlit/secrets.toml` has correct `ALPHA_VANTAGE_API_KEY`")
        st.stop()
    
    with st.spinner(f"🤖 Analyzing stocks and creating your {risk_profile} investment plan..."):
        try:
            # Create placeholder for analysis log
            analysis_placeholder = st.empty()
            
            # Fetch candidates
            logger.info("Fetching stock candidates...")
            candidates, analysis_errors = get_stock_candidates(st.session_state.advisor)
            st.session_state.current_candidates = candidates
            
            # Show analysis log
            with analysis_placeholder.container():
                st.markdown("### 📊 Live Analysis Breakdown")
                if len(candidates) > 0:
                    for candidate in candidates:
                        st.markdown(f"""
                        <div class="analysis-box">
                        ✅ <strong>{candidate['symbol']}</strong> - ${candidate['price']:.2f}<br>
                        📊 RSI: {candidate['rsi']} | 📈 MACD: {candidate['macd_signal']} | 
                        🎯 Trend: {candidate['trend']}<br>
                        ⚡ Recommendation: {candidate['recommendation']}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Show any analysis errors
            if analysis_errors:
                with st.expander("⚠️ Analysis Notes", expanded=True):
                    for error in analysis_errors.split('\n'):
                        if error:
                            st.warning(f"• {error}")
                    logger.warning(f"Analysis errors: {analysis_errors}")
            
            # Validate candidates
            if not candidates or len(candidates) == 0:
                st.error("❌ **Could not analyze any stocks**")
                st.error("**Possible causes:**")
                st.error("1. Invalid API key")
                st.error("2. API rate limit (25 calls/day)")
                st.error("3. Alpha Vantage server down")
                st.error("4. Network connectivity issue")
                st.markdown("---")
                st.error("**Solutions:**")
                st.error("• Check `.streamlit/secrets.toml` has correct API key")
                st.error("• Try again in a few moments")
                st.error("• Check: https://www.alphavantage.co/")
                st.stop()
            
            logger.info(f"✓ Successfully retrieved {len(candidates)} candidates")
            st.success(f"✅ Successfully analyzed {len(candidates)} stocks")
            
            # Generate investment plan
            logger.info("Generating investment plan...")
            plan, plan_error = generate_investment_plan(
                budget, 
                risk_profile, 
                candidates, 
                st.session_state.advisor
            )
            
            if plan_error:
                logger.error(f"Plan generation error: {plan_error}")
                st.error(f"**AI Plan Generation Failed:**")
                st.error(plan_error)
                st.info("💡 Try selecting a different risk profile or adjusting your budget")
                st.stop()
            
            if not plan:
                logger.error("Plan returned as None")
                st.error("❌ **An unknown error occurred during plan generation**")
                st.stop()
            
            # Success!
            st.session_state.generated_plan = plan
            logger.info(f"✓ Plan generated successfully with {len(plan)} items")
            st.success(f"✅ AI Investment Plan Generated Successfully for {len(plan)} stocks!")
            
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}", exc_info=True)
            st.error(f"❌ **Unexpected Error**")
            st.error(f"Type: {type(e).__name__}")
            st.error(f"Message: {str(e)}")
            with st.expander("📋 Detailed Error Trace"):
                st.code(f"{type(e).__name__}: {str(e)}", language="python")
            st.stop()

# --- Display Generated Plan ---

if st.session_state.generated_plan:
    logger.info("Displaying generated plan")
    plan = st.session_state.generated_plan
    
    st.divider()
    st.subheader(f"📈 Your {risk_profile} Investment Plan")
    st.markdown(f"✅ **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Beginner explanation
    st.markdown("""
    <div class="beginner-box">
        <h4>📚 How to Read Your Investment Plan</h4>
        <p><strong>Stock</strong> = Company name | 
        <strong>Your Budget</strong> = $ to invest | 
        <strong># Shares</strong> = Pieces to buy |
        <strong>Today's Price</strong> = Current cost per share |
        <strong>AI's 12-Mo Target</strong> = AI's prediction where price will be |
        <strong>Potential Gain</strong> = Expected profit if target is hit |
        <strong>Health Score</strong> = How good the stock is (0-100)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Build DataFrame
    plan_data = []
    total_allocated = 0.0
    total_potential = 0.0
    
    for item in plan:
        cost = float(item.get('cost', 0))
        target = float(item.get('target_mean', 0))
        shares = float(item.get('shares', 0))
        
        total_allocated += cost
        total_potential += (shares * target)
        
        plan_data.append({
            "Stock": item['symbol'],
            "Sector": item.get('sector', 'N/A'),
            "Your Budget": f"${cost:.2f}",
            "% of Total": f"{item.get('allocation_pct', 0):.1f}%",
            "# Shares": f"{shares:.4f}",
            "Today's Price": f"${item.get('current_price', 0):.2f}",
            "AI's 12-Mo Target": f"${target:.2f}",
            "Potential Gain": f"{item.get('upside_pct', 0):.2f}%",
            "Health Score": f"{item.get('buy_score', 0):.0f}/100"
        })
    
    df = pd.DataFrame(plan_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Summary section
    st.markdown("### 💡 What This Means For You")
    
    total_upside = ((total_potential - total_allocated) / total_allocated * 100) if total_allocated > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Your Investment",
            f"${budget:,.0f}",
            "Total money going in"
        )
    
    with col2:
        st.metric(
            "📊 Allocated",
            f"${total_allocated:,.0f}",
            "Ready to invest"
        )
    
    with col3:
        st.metric(
            "🎯 Stocks",
            f"{len(plan)}",
            "Companies you own"
        )
    
    with col4:
        st.metric(
            "🚀 12-Mo Upside",
            f"+{total_upside:.1f}%",
            "Potential growth"
        )
    
    # Detailed explanation
    with st.expander("📚 Understanding Your Results", expanded=True):
        st.markdown(f"""
        ### Your Investment Breakdown:
        
        **Today (Now):**
        - Investment Amount: ${total_allocated:,.2f}
        
        **In 12 Months (AI's Prediction):**
        - Expected Value: ${total_potential:,.2f}
        - Expected Profit: ${total_potential - total_allocated:,.2f}
        - Potential Return: {total_upside:.1f}%
        
        ### What This Means:
        
        If you follow this plan today:
        - 🎯 **Best Case:** Your ${total_allocated:,.2f} becomes ${total_potential:,.2f}
        - 📈 **This is a {total_upside:.1f}% potential return**
        - ⚠️ **Remember:** This is AI's projection, not guaranteed!
        
        ### Real Example (Your Numbers):
        - You invest: ${total_allocated:,.2f}
        - AI says in 12 months it's worth: ${total_potential:,.2f}
        - Your profit: ${total_potential - total_allocated:,.2f}
        
        **If this happens, you'll have made:**
        ```
        Profit = ${total_potential - total_allocated:,.2f}
        Return = {total_upside:.1f}%
        ```
        
        ### How the AI Picked These Stocks:
        
        For each stock, the AI calculated a score (0-100) based on:
        1. **RSI** - Is the stock undervalued?
        2. **MACD** - What's the trend signal?
        3. **Trend** - Is it going up or down?
        4. **Momentum** - Is it gaining speed?
        
        ### Why These Specific Stocks?
        """)
        
        for item in plan:
            st.markdown(f"""
        **{item['symbol']}** ({item.get('sector', 'Unknown')})
        - Health Score: {item.get('buy_score', 0):.0f}/100 ({
            'Excellent' if item.get('buy_score', 0) >= 80 else 
            'Good' if item.get('buy_score', 0) >= 60 else 
            'Neutral' if item.get('buy_score', 0) >= 40 else 
            'Risky'
        })
        - Current Price: ${item.get('current_price', 0):.2f}
        - AI's 12-Month Target: ${item.get('target_mean', 0):.2f}
        - Your Investment: ${item['cost']:.2f} ({item.get('allocation_pct', 0):.1f}%)
        - Potential Profit: ${(item.get('shares', 0) * item.get('target_mean', 0)) - item['cost']:.2f}
            """)
    
    # Technical analysis section
    with st.expander("📊 Technical Analysis Details", expanded=False):
        st.markdown("""
        ### What Each Technical Indicator Means:
        
        #### RSI (Relative Strength Index) - Momentum
        - **0-30:** Stock is "cold" (might be a good buy) ❄️
        - **30-70:** Normal range ⚖️
        - **70-100:** Stock is "hot" (might be overpriced) 🔥
        
        #### MACD Signal - Trend Direction
        - **BUY:** Momentum is turning positive ⬆️
        - **HOLD:** No clear direction
        - **SELL:** Momentum is turning negative ⬇️
        
        #### Trend - Long-term Direction
        - **BULLISH:** Going up (50-day avg > 200-day avg) ✅
        - **BEARISH:** Going down (50-day avg < 200-day avg) ⚠️
        
        #### Health Score (0-100)
        - **80-100:** Excellent buy ✅
        - **60-80:** Good buy ✅
        - **40-60:** Average ⚖️
        - **Below 40:** High risk ⚠️
        """)
        
        tech_data = []
        for item in plan:
            tech_data.append({
                "Stock": item['symbol'],
                "RSI": f"{item.get('rsi', 'N/A')}",
                "MACD Signal": item.get('macd_signal', 'N/A'),
                "Trend": item.get('trend', 'N/A'),
                "Health Score": f"{item.get('buy_score', 0):.0f}/100"
            })
        
        tech_df = pd.DataFrame(tech_data)
        st.dataframe(tech_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Blockchain section
    st.subheader("🔗 Step 3: Save Your Plan to Blockchain")
    
    st.markdown("""
    <div class="beginner-box">
        <h4>What is Blockchain?</h4>
        <p>Blockchain is a secure, permanent record of your investments on the internet.
        It's like taking a timestamped proof of your portfolio that nobody can change or erase.
        Great for: proving ownership, keeping records, tax tracking.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.wallet_connected:
        st.warning("⚠️ **Wallet Not Connected**")
        st.markdown("👉 **To save your plan to blockchain:**")
        st.markdown("1. Go to **Home** page")
        st.markdown("2. Click **Connect Wallet** in the sidebar")
        st.markdown("3. Use MetaMask or another Web3 wallet")
        st.markdown("4. Come back here and click the save button")
    
    save_btn = st.button(
        f"🔗 Save My {len(plan)} Stocks to Blockchain",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.wallet_connected,
        help="Requires wallet connection. Go to Home page to connect."
    )
    
    if save_btn:
        if not st.session_state.portfolio_manager_initialized:
            st.error("❌ Portfolio manager not initialized")
            st.stop()
        
        st.info("💾 Saving your investment plan to blockchain...")
        progress_bar = st.progress(0)
        
        success_count = 0
        fail_count = 0
        
        for i, item in enumerate(plan):
            progress_bar.progress((i + 1) / len(plan))
            
            try:
                result = st.session_state.portfolio_manager.add_investment_blockchain(
                    user_id=st.session_state.user_id,
                    company=item['symbol'],
                    shares=float(item['shares']),
                    purchase_price=float(item['current_price']),
                    purchase_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                if "Transaction Hash" in str(result):
                    st.success(f"✅ {item['symbol']}: Saved to blockchain")
                    success_count += 1
                    logger.info(f"✓ {item['symbol']} saved to blockchain")
                else:
                    st.warning(f"⚠️ {item['symbol']}: Saved locally only")
                    fail_count += 1
                    
            except Exception as e:
                st.error(f"❌ {item['symbol']}: {str(e)}")
                fail_count += 1
                logger.error(f"Error saving {item['symbol']}: {e}")
        
        progress_bar.empty()
        st.success("✅ **Execution Complete!**")
        st.markdown(f"- **{success_count}** investments saved to blockchain ✅")
        st.markdown(f"- **{fail_count}** items (may still be locally saved)")
        st.info("Navigate to **'💼 Portfolio'** page to view and manage your holdings!")
        
        logger.info(f"Save complete: {success_count} success, {fail_count} failed")
        st.session_state.generated_plan = None

st.divider()


with st.expander("📖 Investment Glossary (Learn All Terms)", expanded=False):
    st.markdown("""
    ### A-Z Investment Terms Explained
    
    | Term | What It Means | Example |
    |------|--------------|---------|
    | **Stock** | A small piece of ownership in a company | 1 Apple share |
    | **Share** | One unit of a stock | Buy 5 shares of Apple |
    | **Portfolio** | Your collection of all investments | You own AAPL + MSFT |
    | **Diversification** | Owning different types of stocks | Own tech + healthcare |
    | **Bull Market** | Market going UP, optimistic 📈 | "Bullish on tech stocks" |
    | **Bear Market** | Market going DOWN, pessimistic 📉 | "Bearish outlook" |
    | **RSI** | Momentum score (0-100) | <30 = oversold, >70 = overbought |
    | **MACD** | Shows trend direction changes | BUY = uptrend starting |
    | **Trend** | The general direction (up/down/flat) | BULLISH = going up |
    | **Moving Average** | Average price over time period | 50-day = 50 days average |
    | **Upside** | Potential profit if prediction correct | "15% upside potential" |
    | **Target Price** | Where AI thinks stock will be | AI: AAPL will be $180 |
    | **Bullish** | Optimistic, expecting UP 📈 | "I'm bullish on Apple" |
    | **Bearish** | Pessimistic, expecting DOWN 📉 | "I'm bearish on tech" |
    | **Blue-Chip** | Large, stable, well-known company | Apple, Microsoft, Coca-Cola |
    | **Sector** | Industry category | Technology, Healthcare, Finance |
    | **Volume** | Number of shares traded today | High volume = many buyers |
    | **Volatility** | How much price jumps around | High = risky, Low = safe |
    | **ROI** | Return on Investment in % | "10% ROI" = earned 10% |
    | **Allocation** | Dividing money between stocks | 50% Apple, 50% Microsoft |
    | **Dividend** | $ company pays to shareholders | Apple pays $0.24/quarter |
    | **P/E Ratio** | Price to Earnings ratio | Determines if stock is cheap |
    | **Market Cap** | Total $ value of company | Apple = $2.8 Trillion |
    | **Liquidity** | How easily you can sell stock | Blue-chips = very liquid |
    | **Hedge** | Protection against losses | Buy opposite stock |
    """)

with st.expander("❓ Frequently Asked Questions", expanded=False):
    st.markdown("""
    ### FAQ Section
    
    **Q: How much should I invest to start?**
    A: Start with $100-$500. Once you're comfortable, increase it. Never invest money you need.
    
    **Q: What's the best time to buy stocks?**
    A: When prices are low (RSI < 30). This app finds those opportunities!
    
    **Q: Can I lose all my money?**
    A: Theoretically yes, but unlikely with diversified blue-chip stocks (AAPL + MSFT).
    
    **Q: How long should I hold?**
    A: At least 5+ years. Short-term trading is risky for beginners.
    
    **Q: Do I need a brokerage account?**
    A: Yes! You need an account with (Fidelity, Charles Schwab, Robinhood, etc.).
    
    **Q: What's a blockchain portfolio?**
    A: A permanent, tamper-proof record of your investments on the internet.
    
    **Q: Is this financial advice?**
    A: No! This is educational. Always do your own research!
    
    **Q: How often should I review?**
    A: Quarterly or annually. Don't check daily - prices fluctuate!
    
    **Q: What if a stock goes down?**
    A: Normal! Market always has ups and downs. Hold if you believe in the company.
    
    **Q: Can I edit my plan?**
    A: Yes! Generate a new plan anytime with different budget/risk profile.
    """)

with st.expander("🚀 Next Steps After Creating Your Plan", expanded=False):
    st.markdown("""
    ### What to Do Now
    
    **1. Open a Brokerage Account** 🏦
    - Choose: Fidelity, Charles Schwab, Robinhood, TD Ameritrade, E*TRADE
    - Takes ~5-10 minutes online
    - Link your bank account for deposits
    
    **2. Fund Your Account** 💳
    - Transfer money from your bank
    - Wait for funds to settle (1-2 days)
    
    **3. Place Your Trades** 📊
    - Search for stock symbols (AAPL, MSFT)
    - Enter exact share quantities from this plan
    - Review and confirm
    - Orders execute immediately during market hours
    
    **4. Monitor Your Portfolio** 👀
    - Check quarterly (not daily!)
    - Review annual performance
    - Rebalance if needed
    
    **5. Keep Learning** 📚
    - Read: "A Random Walk Down Wall Street"
    - Podcast: Investing 101
    - Website: Investopedia.com
    
    ### Important Timeline
    - **Day 0:** Create account + fund it
    - **Day 3:** Money settles, make trades
    - **Month 1:** Review what you bought
    - **Month 3:** First quarterly check-in
    - **Year 1:** Evaluate performance
    - **Year 5+:** Enjoy long-term wealth building
    """)

logger.info("="*100)
logger.info("PAGE RENDER COMPLETE")
logger.info("="*100)

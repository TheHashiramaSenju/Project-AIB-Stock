"""
AI Portfolio Budgeter - Alpha Vantage Edition (2-Stock Optimized)
================================================================
This page allows a user to input a budget and risk profile, and receive
a fully-allocated investment plan based on AI analysis using Alpha Vantage.

OPTIMIZED FOR FREE TIER: Only All stocks (2 for now) = 2 API calls (out of 25/day limit)

Features:
- Uses Alpha Vantage for technical analysis (RSI, MACD, trend analysis)
- Generates a diversified plan based on risk profile
- Allows one-click saving of the entire plan to the blockchain portfolio
- Full integration with existing portfolio management system
- Enhanced error handling, diagnostics, and logging
- Robust initialization and validation

Author: Bhoomika M
Date: 2025-11-08
Version: 2.0 (Robust)
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
    st.error("- `stock_advisor_alphavantage.py`")
    st.error("- `ai_budgeter.py`")
    st.error("- `portfolio_manager.py`")
    st.error("- `blockchain_integration.py`")
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Budgeting - AI Stock Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    .sub-header {
        text-align: center;
        color: #1f77b4 !important;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    
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

    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .debug-box {
        background: #f0f0f0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ff7f0e;
        font-family: monospace;
        font-size: 0.85rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization (Robust) ---
def init_session_state():
    """
    Initialize all session state variables with comprehensive error handling.
    This function is called at app startup and handles all initialization logic.
    """
    
    logger.info("=" * 80)
    logger.info("INITIALIZING SESSION STATE")
    logger.info("=" * 80)
    
    # ===== Alpha Vantage API Key =====
    if 'alpha_vantage_key' not in st.session_state:
        try:
            api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                # Fallback to environment variable
                api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                # Default key
                api_key = "ZRBAZ10IY283K3T7"
            
            st.session_state.alpha_vantage_key = api_key
            source = "secrets" if st.secrets.get("ALPHA_VANTAGE_API_KEY") else "environment/default"
            st.session_state.api_key_source = source
            st.session_state.api_key_configured = True
            
            logger.info(f"✓ API Key configured from: {source}")
            logger.info(f"✓ API Key (first 10 chars): {api_key[:10]}...")
            
        except Exception as e:
            logger.error(f"✗ Error loading API key: {e}")
            st.session_state.alpha_vantage_key = "ZRBAZ10IY283K3T7"
            st.session_state.api_key_source = "default"
            st.session_state.api_key_configured = False
    
    # ===== StockAdvisorAlphaVantage =====
    if 'advisor' not in st.session_state:
        try:
            st.session_state.advisor = StockAdvisorAlphaVantage(
                st.session_state.alpha_vantage_key
            )
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
    
    # ===== Wallet Status =====
    if 'wallet_connected' not in st.session_state:
        st.session_state.wallet_connected = False
        logger.info("✓ Wallet status initialized")
    
    # ===== Blockchain Configuration =====
    if 'contract_address' not in st.session_state:
        st.session_state.contract_address = st.secrets.get("CONTRACT_ADDRESS", "")
        st.session_state.rpc_url = st.secrets.get("RPC_URL", "")
        logger.info("✓ Blockchain configuration loaded")
    
    # ===== User ID =====
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "streamlit_user"
        logger.info("✓ User ID initialized")
    
    # ===== Generated Plan =====
    if 'generated_plan' not in st.session_state:
        st.session_state.generated_plan = None
        logger.info("✓ Generated plan state initialized")
    
    # ===== API Call Counter =====
    if 'api_calls_today' not in st.session_state:
        st.session_state.api_calls_today = 0
        logger.info("✓ API call counter initialized")
    
    logger.info("=" * 80)
    logger.info("SESSION STATE INITIALIZATION COMPLETE")
    logger.info("=" * 80)

# Initialize session state
try:
    init_session_state()
except Exception as e:
    logger.error(f"Critical error during session state initialization: {e}")
    st.error("🚨 **Fatal Error During Initialization**")
    st.error(f"Details: {str(e)}")
    st.stop()

# --- API Health Check Function ---
def check_api_health(api_key: str) -> Dict[str, Any]:
    """
    Tests Alpha Vantage API connectivity with comprehensive diagnostics.
    
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
                "code": "INVALID_KEY"
            }
        
        if "Note" in data:
            note_msg = data['Note']
            logger.warning(f"Rate limit: {note_msg}")
            return {
                "status": "rate_limited",
                "message": "Rate Limit Reached",
                "details": note_msg,
                "code": "RATE_LIMITED"
            }
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            if quote and quote.get("05. price"):
                logger.info(f"✓ API Health Check PASSED - AAPL Price: {quote['05. price']}")
                return {
                    "status": "success",
                    "message": "✅ API is working correctly",
                    "details": f"Successfully retrieved AAPL quote: ${quote['05. price']}",
                    "code": "HEALTHY"
                }
        
        logger.warning("Unexpected API response structure")
        return {
            "status": "unknown",
            "message": "Unexpected API Response",
            "details": f"Response structure unexpected. Keys: {list(data.keys())}",
            "code": "UNKNOWN_RESPONSE"
        }
        
    except requests.exceptions.Timeout:
        logger.error("API request timeout")
        return {
            "status": "error",
            "message": "Connection Timeout",
            "details": "Alpha Vantage server did not respond in time",
            "code": "TIMEOUT"
        }
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to API")
        return {
            "status": "error",
            "message": "Cannot Connect to API",
            "details": "Check your internet connection",
            "code": "NO_CONNECTION"
        }
    except Exception as e:
        logger.error(f"Unexpected error in health check: {e}")
        return {
            "status": "error",
            "message": f"Health Check Error: {type(e).__name__}",
            "details": str(e),
            "code": "HEALTH_CHECK_ERROR"
        }

# --- Stock Analysis Function ---
@st.cache_data(ttl=3600)
def get_stock_candidates(_advisor: StockAdvisorAlphaVantage) -> Tuple[List[Dict], str]:
    """
    Analyzes All stocks (2 for now) with comprehensive error handling.
    
    Args:
        _advisor: StockAdvisorAlphaVantage instance
        
    Returns:
        Tuple of (candidates_list, error_summary_string)
    """
    
    logger.info("=" * 80)
    logger.info("STARTING STOCK ANALYSIS")
    logger.info("=" * 80)
    
    if _advisor is None:
        error = "Advisor not initialized. Cannot analyze stocks."
        logger.error(f"✗ {error}")
        return [], error
    
    stock_universe = {
        'AAPL': 'Technology',
        'MSFT': 'Technology'
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
            
            # Call the analysis function
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
            
            # Build candidate record
            candidate = {
                'symbol': symbol,
                'name': symbol,
                'sector': sector,
                'price': float(price),
                'change_percent': str(analysis.get('change_percent', '0%')),
                'rsi': analysis.get('rsi'),
                'macd_signal': analysis.get('macd_signal', 'HOLD'),
                'trend': analysis.get('trend', 'NEUTRAL'),
                'recommendation': analysis.get('recommendation', 'HOLD'),
                'volume': int(analysis.get('volume', 0)),
                'high': float(analysis.get('high', 0)),
                'low': float(analysis.get('low', 0)),
                'change': float(analysis.get('change', 0))
            }
            
            candidates.append(candidate)
            analysis_count += 1
            
            logger.info(f"✓ {symbol} analyzed successfully - Price: ${price}")
            status_placeholder.success(f"✓ {symbol} analyzed successfully")
            
            # Rate limit delay
            if i < total_stocks - 1:
                time.sleep(2)
            
        except Exception as e:
            error = f"{symbol}: {type(e).__name__}: {str(e)}"
            errors.append(error)
            logger.error(f"✗ Exception while analyzing {symbol}: {e}")
    
    progress_bar.empty()
    status_placeholder.empty()
    
    # Summary logging
    logger.info("=" * 80)
    logger.info(f"STOCK ANALYSIS COMPLETE")
    logger.info(f"Successfully analyzed: {analysis_count}/{total_stocks}")
    logger.info(f"Errors encountered: {len(errors)}")
    for error in errors:
        logger.warning(f"  - {error}")
    logger.info("=" * 80)
    
    error_text = "\n".join(errors) if errors else ""
    return candidates, error_text

# --- Investment Plan Generation ---
def generate_investment_plan(budget: float, risk_profile: str, 
                            candidates: List[Dict], 
                            advisor: StockAdvisorAlphaVantage) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Generates investment plan using AIBudgeter.
    
    Args:
        budget: Total investment budget
        risk_profile: Risk profile selection
        candidates: List of analyzed stocks
        advisor: Stock advisor instance
        
    Returns:
        Tuple of (plan, error_message)
    """
    
    logger.info("=" * 80)
    logger.info("STARTING PLAN GENERATION")
    logger.info(f"Budget: ${budget:.2f}, Risk Profile: {risk_profile}")
    logger.info(f"Candidates: {len(candidates)} stocks")
    logger.info("=" * 80)
    
    if not candidates or len(candidates) == 0:
        error = "No stock candidates available for analysis."
        logger.error(f"✗ {error}")
        return None, error
    
    try:
        # Initialize budgeter
        budgeter = AIBudgeter()
        budgeter.set_verbose(True)
        
        logger.info(f"AIBudgeter initialized")
        logger.info(f"Generating plan for {risk_profile} profile with ${budget:.2f}...")
        
        # Generate plan
        plan, error = budgeter.generate_investment_plan(budget, risk_profile, candidates)
        
        if error:
            logger.error(f"✗ AIBudgeter error: {error}")
            return None, error
        
        if not plan:
            error = "Plan generation returned no results."
            logger.error(f"✗ {error}")
            return None, error
        
        # Validate and enrich plan
        for idx, item in enumerate(plan):
            if 'sector' not in item:
                item['sector'] = 'Unknown'
            logger.info(f"  [{idx+1}] {item['symbol']}: ${item['cost']:.2f} "
                       f"({item['allocation_pct']:.1f}%) - Upside: {item['upside_pct']:.1f}%")
        
        logger.info("=" * 80)
        logger.info(f"PLAN GENERATION COMPLETE - {len(plan)} items")
        logger.info("=" * 80)
        
        return plan, None
        
    except Exception as e:
        error = f"Plan generation error: {type(e).__name__}: {str(e)}"
        logger.error(f"✗ {error}")
        return None, error

# --- MAIN UI ---

# System Diagnostics Expander (Top)
with st.expander("🔧 **System Diagnostics** (Click to expand)", expanded=False):
    st.markdown("### ⚙️ System Status Check")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**API Configuration:**")
        if st.session_state.api_key_configured:
            st.success(f"✅ Source: {st.session_state.api_key_source}")
            st.code(f"{st.session_state.alpha_vantage_key[:10]}...***", language="text")
        else:
            st.error("❌ API Key not properly configured")
    
    with col2:
        st.markdown("**Advisor Status:**")
        if st.session_state.advisor_initialized:
            st.success("✅ Initialized")
        else:
            st.error(f"❌ Error: {st.session_state.advisor_error}")
    
    with col3:
        st.markdown("**Portfolio Manager:**")
        if st.session_state.portfolio_manager_initialized:
            st.success("✅ Initialized")
        else:
            st.error("❌ Not initialized")
    
    st.markdown("---")
    st.markdown("### 🧪 API Connectivity Test")
    
    if st.button("Test Alpha Vantage API Connection", key="api_test"):
        with st.spinner("Testing API connection..."):
            health = check_api_health(st.session_state.alpha_vantage_key)
            
            logger.info(f"Health check result: {health['code']}")
            
            if health['status'] == 'success':
                st.success(f"✅ {health['message']}")
                st.info(health['details'])
            elif health['status'] == 'rate_limited':
                st.warning(f"⚠️ {health['message']}")
                st.warning(health['details'])
                st.info("💡 **Solution:** Wait 60 seconds and try again, or wait until tomorrow (UTC midnight)")
            else:
                st.error(f"❌ {health['message']}")
                st.error(health['details'])
                st.error("**Troubleshooting:**")
                st.error("1. Verify API key in `.streamlit/secrets.toml`")
                st.error("2. Check internet connectivity")
                st.error("3. Verify Alpha Vantage API is operational")
    
    st.markdown("---")
    st.markdown("### 📊 Usage Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("API Calls Today", st.session_state.api_calls_today or 0, "out of 25")
    with col2:
        st.metric("Remaining Today", 25 - (st.session_state.api_calls_today or 0), "calls")
    with col3:
        st.metric("Per Minute", 5, "call limit")

# Main Info Box
st.markdown("""
<div class="info-box">
    <h3>🤖 AI Portfolio Budgeter (Optimized for Alpha Vantage)</h3>
    <p>This AI-powered tool analyzes <strong>2 premium stocks</strong> (AAPL + MSFT) using technical indicators 
    (RSI, MACD, trend analysis) from <strong>Alpha Vantage</strong>. It generates a personalized investment plan 
    based on your budget and risk tolerance. <strong>Minimal API usage = No rate limits!</strong></p>
</div>
""", unsafe_allow_html=True)

st.subheader("1️⃣ Configure Your Investment Plan")

col1, col2 = st.columns(2)

with col1:
    budget = st.number_input(
        "Enter Your Total Investment Budget ($)",
        min_value=100.0,
        max_value=1000000.0,
        value=1000.0,
        step=100.0,
        help="Enter the total amount you want to invest (minimum $100, maximum $1,000,000)."
    )
    logger.info(f"User entered budget: ${budget:.2f}")

with col2:
    risk_profile = st.selectbox(
        "Select Your Risk Profile",
        ['Conservative', 'Moderate', 'Aggressive'],
        index=1,
        help="**Conservative**: Broad diversification (5-7 stocks), stable sectors, low volatility\n"
             "**Moderate**: Balanced (3-5 stocks), mix of growth and stability\n"
             "**Aggressive**: Concentrated (2-3 stocks), high-growth sectors, high volatility"
    )
    logger.info(f"User selected risk profile: {risk_profile}")

generate_btn = st.button(
    "🚀 Generate AI Investment Plan",
    type="primary",
    use_container_width=True,
    key="generate_plan"
)

st.divider()

# --- PLAN GENERATION LOGIC ---
if generate_btn:
    logger.info("=" * 80)
    logger.info("USER CLICKED: GENERATE PLAN")
    logger.info("=" * 80)
    
    st.session_state.generated_plan = None
    
    # Pre-flight checks
    if not st.session_state.advisor_initialized:
        st.error("🚨 **Critical Error: Advisor Not Initialized**")
        st.error("The stock advisor failed to initialize.")
        st.error(f"Details: {st.session_state.advisor_error}")
        st.error("**Solution:**")
        st.error("1. Check `.streamlit/secrets.toml` has `ALPHA_VANTAGE_API_KEY`")
        st.error("2. Restart Streamlit")
        st.error("3. Run API test in Diagnostics above")
        logger.error("Preflight check failed: Advisor not initialized")
        st.stop()
    
    with st.spinner(f"🤖 **Analyzing All stocks (2 for now)...** Generating a '{risk_profile}' plan for **${budget:,.2f}**..."):
        try:
            # Get candidates
            logger.info("Fetching stock candidates...")
            candidates, analysis_errors = get_stock_candidates(st.session_state.advisor)
            
            # Show any analysis warnings
            if analysis_errors:
                with st.expander("⚠️ Analysis Warnings", expanded=True):
                    st.warning("The following issues occurred during analysis:")
                    for error in analysis_errors.split('\n'):
                        if error:
                            st.warning(f"• {error}")
                    logger.warning(f"Analysis errors: {analysis_errors}")
            
            # Validate candidates
            if not candidates or len(candidates) == 0:
                logger.error("No candidates returned from analysis")
                st.error("❌ **Could not analyze any stocks**")
                st.error("**Possible causes:**")
                st.error("1. ❌ Invalid or missing API key")
                st.error("2. ❌ API rate limit exceeded (25 calls/day, 5 calls/minute)")
                st.error("3. ❌ Alpha Vantage server temporarily down")
                st.error("4. ❌ Network connectivity issue")
                st.error("5. ❌ Firewall or security software blocking requests")
                st.markdown("---")
                st.error("**Solutions:**")
                st.error("• Run the API test in the Diagnostics tab above")
                st.error("• If rate limited: Wait 60 seconds or until tomorrow (UTC midnight)")
                st.error("• Check `.streamlit/secrets.toml` has correct API key")
                st.error("• Restart Streamlit after any configuration changes")
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
            logger.error(f"Unexpected error during plan generation: {type(e).__name__}: {e}", exc_info=True)
            st.error(f"❌ **Unexpected Error**")
            st.error(f"Type: {type(e).__name__}")
            st.error(f"Message: {str(e)}")
            with st.expander("📋 Detailed Error Trace"):
                st.code(f"{type(e).__name__}: {str(e)}", language="python")
            st.stop()

# --- DISPLAY GENERATED PLAN ---
if st.session_state.generated_plan:
    logger.info("Displaying generated plan")
    plan = st.session_state.generated_plan
    
    st.subheader(f"📈 Your {risk_profile} AI Investment Plan")
    st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Build DataFrame
    plan_data = []
    total_allocated = 0.0
    total_potential_value = 0.0
    
    for item in plan:
        try:
            cost = float(item.get('cost', 0))
            target = float(item.get('target_mean', 0))
            shares = float(item.get('shares', 0))
            
            total_allocated += cost
            total_potential_value += (shares * target)
            
            plan_data.append({
                "Stock": item['symbol'],
                "Sector": item.get('sector', 'N/A'),
                "Allocation ($)": f"${cost:.2f}",
                "% Portfolio": f"{item.get('allocation_pct', 0):.1f}%",
                "Shares": f"{shares:.4f}",
                "Price": f"${item.get('current_price', 0):.2f}",
                "Target": f"${target:.2f}",
                "Upside %": f"{item.get('upside_pct', 0):.2f}%",
                "Tech Score": f"{item.get('buy_score', 0):.0f}/100"
            })
        except Exception as e:
            logger.error(f"Error processing plan item {item.get('symbol', 'UNKNOWN')}: {e}")
    
    if plan_data:
        df = pd.DataFrame(plan_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Summary metrics
        total_upside = ((total_potential_value - total_allocated) / total_allocated * 100) if total_allocated > 0 else 0
        
        st.markdown("---")
        st.markdown("### 📊 Plan Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 Total Budget", f"${budget:,.2f}")
        col2.metric("💰 Allocated", f"${total_allocated:,.2f}")
        col3.metric("📈 Stocks", f"{len(plan)}")
        col4.metric("🎯 Est. Upside", f"{total_upside:,.1f}%")
        
        st.markdown("---")
        
        # Technical Details
        with st.expander("📊 Detailed Technical Analysis", expanded=False):
            tech_data = []
            for item in plan:
                tech_data.append({
                    "Stock": item['symbol'],
                    "RSI": f"{item.get('rsi', 'N/A')}",
                    "MACD": item.get('macd_signal', 'N/A'),
                    "Trend": item.get('trend', 'N/A'),
                    "Score": f"{item.get('buy_score', 0):.0f}/100"
                })
            
            tech_df = pd.DataFrame(tech_data)
            st.dataframe(tech_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Blockchain Section
        st.subheader("2️⃣ Save to Blockchain Portfolio")
        st.markdown("Save this investment plan to your blockchain portfolio with one click.")
        
        if not st.session_state.wallet_connected:
            st.warning("⚠️ **Wallet Not Connected**")
            st.warning("Please connect your wallet via the 'Home' page sidebar before saving.")
        
        save_btn = st.button(
            f"🔗 Save {len(plan)} Investments to Blockchain",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.wallet_connected,
            key="save_to_blockchain"
        )
        
        if save_btn:
            if not st.session_state.portfolio_manager_initialized:
                st.error("❌ Portfolio manager not initialized")
                logger.error("Portfolio manager not initialized when attempting save")
                st.stop()
            
            logger.info(f"Saving {len(plan)} investments to blockchain...")
            st.info("Executing plan and saving investments to blockchain...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            fail_count = 0
            
            for i, item in enumerate(plan):
                symbol = item['symbol']
                progress_bar.progress((i + 1) / len(plan))
                status_text.write(f"Processing {symbol}... ({i+1}/{len(plan)})")
                
                try:
                    result = st.session_state.portfolio_manager.add_investment_blockchain(
                        user_id=st.session_state.user_id,
                        company=symbol,
                        shares=float(item['shares']),
                        purchase_price=float(item['current_price']),
                        purchase_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    
                    if "Transaction Hash" in str(result):
                        st.success(f"✅ {symbol}: Saved to blockchain")
                        success_count += 1
                        logger.info(f"✓ {symbol} saved to blockchain")
                    else:
                        st.warning(f"⚠️ {symbol}: Saved locally only")
                        fail_count += 1
                        logger.warning(f"⚠ {symbol} saved locally only")
                        
                except Exception as e:
                    st.error(f"❌ {symbol}: Error - {str(e)}")
                    fail_count += 1
                    logger.error(f"✗ Error saving {symbol}: {e}")
            
            progress_bar.empty()
            status_text.empty()
            
            st.success("✅ **Execution Complete!**")
            st.markdown(f"- **{success_count}** investments saved to blockchain")
            st.markdown(f"- **{fail_count}** failed or saved locally")
            st.info("Navigate to **'💼 Portfolio'** page to view your holdings")
            
            logger.info(f"Save complete: {success_count} success, {fail_count} failed")
            st.session_state.generated_plan = None

st.divider()

# --- Educational Content ---
with st.expander("📚 Understanding Risk Profiles", expanded=False):
    st.markdown("""
    ### 🛡️ Conservative Profile
    - **Goal:** Capital preservation with modest growth
    - **Diversification:** 5-7 stocks
    - **Sectors:** Utilities, Consumer Defensive, Healthcare, Financials
    - **Tech Score Minimum:** 60/100
    - **Best for:** Risk-averse investors, retirees, capital preservation
    
    ### ⚖️ Moderate Profile
    - **Goal:** Balanced growth with stability
    - **Diversification:** 3-5 stocks
    - **Sectors:** Mix of stable and growth (Tech, Consumer, Healthcare, Finance)
    - **Tech Score Minimum:** 70/100
    - **Best for:** Most investors, long-term growth seekers
    
    ### 🚀 Aggressive Profile
    - **Goal:** Maximum capital growth
    - **Diversification:** 2-3 stocks
    - **Sectors:** Technology, Consumer Cyclical (high-growth)
    - **Tech Score Minimum:** 80/100
    - **Best for:** Experienced investors, long time horizon, high risk tolerance
    """)

with st.expander("❓ How the AI Budgeter Works", expanded=False):
    st.markdown("""
    ### 6-Step AI Process:
    
    **1. Define Universe**
    - Analyzes 2 premium stocks: AAPL + MSFT
    - High liquidity, reliable data
    
    **2. Technical Analysis**
    - RSI (Relative Strength Index): 0-100 momentum scale
    - MACD: Moving Average Convergence Divergence
    - Trend: 50-day vs 200-day moving averages
    - Momentum: Daily price changes
    
    **3. Calculate Score (0-100)**
    - RSI: 0-30 pts (oversold to overbought)
    - MACD: 0-30 pts (sell to buy signals)
    - Trend: 0-20 pts (bearish to bullish)
    - Momentum: 0-20 pts (negative to positive)
    
    **4. Filter by Risk Profile**
    - Conservative: Min 60/100, stable sectors
    - Moderate: Min 70/100, balanced sectors
    - Aggressive: Min 80/100, growth sectors
    
    **5. Rank & Select**
    - Weighted score: 60% technical + 40% upside
    - Select top stocks matching criteria
    
    **6. Allocate Budget**
    - Conservative/Moderate: Equal weight
    - Aggressive: Weighted (50/30/20 split)
    - Calculate exact shares to purchase
    """)

with st.expander("🔑 API & Rate Limits", expanded=False):
    st.markdown("""
    ### Alpha Vantage Free Tier:
    - **Daily Limit:** 25 API calls/day
    - **Rate Limit:** 5 API calls/minute
    - **Reset:** UTC Midnight daily
    
    ### This App Usage:
    - **Calls Per Run:** 2 (one per stock)
    - **Daily Usage:** 8% of limit (2 out of 25)
    - **Per-Minute Usage:** 40% of limit (2 out of 5)
    - **No Throttling:** Complete in seconds
    
    ### Premium Tier Options:
    - 30+ calls/minute - $29.99/month
    - 75+ calls/minute - $49.99/month
    - 300+ calls/minute - $99.99/month
    - Unlimited - $249.99/month
    """)

with st.expander("🆘 Troubleshooting", expanded=False):
    st.markdown("""
    ### ❌ "Failed to analyze any stocks"
    **Causes:** Invalid API key, rate limit, server down, network issue
    **Solutions:**
    1. Run API test in Diagnostics
    2. Check `.streamlit/secrets.toml` has correct key
    3. Wait 60 seconds if rate limited
    4. Check internet connection
    
    ### ❌ "Could not fetch stock candidates"
    **Causes:** Network connectivity, Alpha Vantage server down
    **Solutions:**
    1. Check internet connection
    2. Try again in a few moments
    3. Check Alpha Vantage status: alphavantage.co
    
    ### ❌ ImportError on modules
    **Cause:** Missing required Python files
    **Solution:** Ensure these files exist in `streamlit_app/`:
    - `stock_advisor_alphavantage.py`
    - `ai_budgeter.py`
    - `portfolio_manager.py`
    - `blockchain_integration.py`
    
    ### ✅ Still need help?
    - Check browser console (F12) for errors
    - Review Streamlit logs for detailed messages
    - Run diagnostics check at top of page
    """)

logger.info("=" * 80)
logger.info("PAGE RENDER COMPLETE")
logger.info("=" * 80)
